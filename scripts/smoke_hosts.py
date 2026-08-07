#!/usr/bin/env python3
"""Run opt-in, isolated live compatibility smokes.

This script uses existing local client authentication. It never prints credentials,
never enables write tools for Claude/Codex/Pi, and gives Hermes a disposable home.
Live calls may consume provider quota.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "fixtures"
RESULTS = ROOT / "evals" / "results"
HOST_FIXTURE = {
    "claude": "anger-no-tone-policing",
    "codex": "ambiguous-evidence",
    "pi": "anger-no-tone-policing",
    "hermes": "ambiguous-evidence",
}
HOST_LABEL = {
    "claude": "Claude Code",
    "codex": "OpenAI Codex",
    "pi": "Pi",
    "hermes": "Hermes Agent",
}
SECRETISH = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]+|sk-[A-Za-z0-9_-]+|Bearer\s+\S+)",
    re.IGNORECASE,
)
EMAILISH = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)


def fixture_prompt(host: str) -> tuple[str, str]:
    fixture_id = HOST_FIXTURE[host]
    item = json.loads((FIXTURES / f"{fixture_id}.json").read_text(encoding="utf-8"))
    text = (
        "Synthetic compatibility fixture. This is the first feedback turn. "
        f"Host: {HOST_LABEL[host]}. Context: {item['context']} "
        f"Feedback: {item['feedback']} "
        "Diagnose and produce the approval-gated plan. Do not write files."
    )
    return fixture_id, text


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def safe_error(completed: subprocess.CompletedProcess[str]) -> str:
    text = (completed.stderr or completed.stdout or "no diagnostic output").strip()
    text = SECRETISH.sub("[REDACTED]", text)
    text = EMAILISH.sub("[REDACTED_EMAIL]", text)
    text = text.replace(str(Path.home()), "~")
    if "401" in text or "authentication" in text.lower() or "not logged" in text.lower():
        return "authentication unavailable or expired"
    return text.splitlines()[0][:240] if text else "unknown failure"


def install(target: str, *, project_root: Path | None = None, home: Path | None = None) -> None:
    command = [sys.executable, str(ROOT / "scripts" / "install.py"), "--target", target]
    if project_root:
        command += ["--scope", "project", "--project-root", str(project_root)]
    if home:
        command += ["--home", str(home)]
    completed = run(command, cwd=ROOT)
    if completed.returncode:
        raise RuntimeError(f"installer failed: {safe_error(completed)}")


def score(host: str, fixture_id: str) -> bool:
    completed = run(
        [sys.executable, str(ROOT / "scripts" / "evaluate.py"), "--responses", str(RESULTS / host), "--ids", fixture_id],
        cwd=ROOT,
        timeout=60,
    )
    print(completed.stdout.rstrip())
    return completed.returncode == 0


def smoke_claude() -> tuple[str, str]:
    fixture_id, prompt = fixture_prompt("claude")
    completed = run(
        [
            "claude", "-p", "--plugin-dir", str(ROOT),
            "--permission-mode", "plan", "--tools", "Read",
            "--max-budget-usd", "0.50", "--output-format", "text",
            f"/feedback-loop:feedback {prompt}",
        ],
        cwd=ROOT,
    )
    if completed.returncode:
        raise RuntimeError(safe_error(completed))
    return fixture_id, completed.stdout


def smoke_codex(temp: Path) -> tuple[str, str]:
    fixture_id, prompt = fixture_prompt("codex")
    project = temp / "codex-project"
    project.mkdir()
    install("codex", project_root=project)
    output = temp / "codex-response.txt"
    completed = run(
        [
            "npx", "-y", "@openai/codex@0.147.0", "exec",
            "--ephemeral", "--ignore-user-config", "--sandbox", "read-only",
            "--skip-git-repo-check", "--color", "never", "-C", str(project),
            "-o", str(output), f"$feedback {prompt}",
        ],
        cwd=ROOT,
    )
    if completed.returncode:
        raise RuntimeError(safe_error(completed))
    return fixture_id, output.read_text(encoding="utf-8")


def smoke_pi() -> tuple[str, str]:
    fixture_id, prompt = fixture_prompt("pi")
    completed = run(
        [
            "npx", "-y", "@earendil-works/pi-coding-agent@0.84.1",
            "-p", "--mode", "text", "--no-session", "--no-extensions",
            "--tools", "read", "--provider", "openai-codex", "--model", "gpt-5.4-mini",
            "--skill", str(ROOT / "skills" / "feedback"),
            "--prompt-template", str(ROOT / "prompts" / "feedback.md"),
            f"/feedback {prompt}",
        ],
        cwd=ROOT,
    )
    if completed.returncode:
        raise RuntimeError(safe_error(completed))
    return fixture_id, completed.stdout


def smoke_hermes(temp: Path) -> tuple[str, str]:
    fixture_id, prompt = fixture_prompt("hermes")
    fake_user = temp / "hermes-user"
    hermes_home = fake_user / ".hermes"
    hermes_home.mkdir(parents=True)
    real_home = Path.home() / ".hermes"
    for name in ["config.yaml", "auth.json"]:
        source = real_home / name
        if source.is_file():
            (hermes_home / name).symlink_to(source)
    install("hermes", home=fake_user)
    project = temp / "hermes-project"
    project.mkdir()
    env = dict(os.environ)
    env["HERMES_HOME"] = str(hermes_home)
    completed = run(
        ["hermes", "chat", "-Q", "-t", "file,skills", "-q", f"/feedback {prompt}"],
        cwd=project,
        env=env,
    )
    if completed.returncode:
        raise RuntimeError(safe_error(completed))
    return fixture_id, completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["claude", "codex", "pi", "hermes", "all"], required=True)
    args = parser.parse_args()
    hosts = list(HOST_FIXTURE) if args.host == "all" else [args.host]
    failures = 0
    with tempfile.TemporaryDirectory(prefix="feedback-host-smoke-") as raw_temp:
        temp = Path(raw_temp)
        for host in hosts:
            print(f"\n== {HOST_LABEL[host]} ==")
            required_command = "npx" if host in {"codex", "pi"} else host
            if not shutil.which(required_command):
                print(f"BLOCKED  client executable not found: {required_command}")
                failures += 1
                continue
            try:
                if host == "claude":
                    fixture_id, response = smoke_claude()
                elif host == "codex":
                    fixture_id, response = smoke_codex(temp)
                elif host == "pi":
                    fixture_id, response = smoke_pi()
                else:
                    fixture_id, response = smoke_hermes(temp)
                output_dir = RESULTS / host
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / f"{fixture_id}.txt").write_text(response, encoding="utf-8")
                if not score(host, fixture_id):
                    failures += 1
            except subprocess.TimeoutExpired:
                print("FAIL  client timed out")
                failures += 1
            except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
                print(f"BLOCKED  {exc}")
                failures += 1
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
