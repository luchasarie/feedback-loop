#!/usr/bin/env python3
"""Dependency-free repository validator for Feedback Loop."""
from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "feedback" / "SKILL.md"
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata"}
PRIVATE_PATTERNS = {
    "absolute home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "private vault name": re.compile(r"Magma Knight|Luchas Arie - The", re.IGNORECASE),
    "private Hermes profile path": re.compile(r"\.hermes/profiles/[A-Za-z0-9._-]+"),
    "GitHub token-like secret": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "OpenAI key-like secret": re.compile(r"sk-[A-Za-z0-9_-]{24,}"),
}
CANARY_ALLOWLIST: set[str] = set()

class Report:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []

    def check(self, condition: bool, label: str, detail: str = "") -> None:
        if condition:
            self.passed.append(label)
        else:
            self.failed.append(label + (f": {detail}" if detail else ""))


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md does not start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    raw = text[4:end]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, text[end + 5 :]


def local_links(path: Path, text: str) -> list[tuple[str, Path]]:
    links: list[tuple[str, Path]] = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        clean = target.split("#", 1)[0].strip()
        if not clean or re.match(r"(?:https?|mailto):", clean):
            continue
        links.append((target, (path.parent / clean).resolve()))
    return links


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", header[16:24])


def validate_skill(report: Report) -> None:
    text = SKILL.read_text(encoding="utf-8")
    contract_text = "\n".join(
        [text]
        + [
            path.read_text(encoding="utf-8")
            for path in sorted((SKILL.parent / "references").rglob("*.md"))
        ]
    )
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as exc:
        report.check(False, "Agent Skills frontmatter", str(exc))
        return

    report.check(set(fm) <= ALLOWED_FRONTMATTER, "frontmatter keys are portable", str(sorted(set(fm) - ALLOWED_FRONTMATTER)))
    report.check(fm.get("name") == "feedback", "canonical skill name")
    desc = fm.get("description", "")
    report.check(1 <= len(desc) <= 1024, "description length", str(len(desc)))
    report.check(bool(re.fullmatch(r"[a-z0-9-]{1,64}", fm.get("name", ""))), "skill name syntax")
    report.check(len(text.splitlines()) <= 500, "progressive-disclosure line budget", str(len(text.splitlines())))

    required = {
        "plan-only gate": "feedback turn is read-only",
        "approval status": "AWAITING APPROVAL",
        "no-change sentence": "No changes have been applied",
        "anger contract": "tone-policing",
        "unknown host fallback": "Host: Unknown",
        "redaction": "[REDACTED]",
        "whole-plan approval": "APPROVE ALL",
        "item approval": "APPROVE F1,F3",
        "item rejection": "REJECT F4",
        "collaboration contract": "Agent commitment",
        "later verification": "Run each item's verification",
    }
    for label, needle in required.items():
        report.check(needle in contract_text, f"skill contract: {label}")

    refs = [
        "hosts/hermes.md", "hosts/claude-code.md", "hosts/codex.md",
        "hosts/pi.md", "hosts/generic.md", "routing.md",
        "approval-protocol.md", "privacy.md",
    ]
    for rel in refs:
        report.check((SKILL.parent / "references" / rel).is_file(), f"reference exists: {rel}")

    for target, resolved in local_links(SKILL, body):
        report.check(resolved.is_file(), f"SKILL link resolves: {target}", str(resolved))


def validate_markdown_links(report: Report) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target, resolved in local_links(path, text):
            report.check(resolved.exists(), f"link resolves: {path.relative_to(ROOT)} -> {target}")


def validate_metadata(report: Report) -> None:
    for rel in ["package.json", ".claude-plugin/plugin.json"]:
        path = ROOT / rel
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.check(False, f"valid JSON: {rel}", str(exc))
            continue
        report.check(data.get("version") == "1.0.0", f"version pinned: {rel}")
        report.check(data.get("license") == "MIT", f"license declared: {rel}")
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pi_skills = package.get("pi", {}).get("skills", [])
    report.check(
        "./skills" in pi_skills or "./skills/feedback" in pi_skills,
        "Pi package exports canonical skill",
    )
    report.check("./prompts" in package.get("pi", {}).get("prompts", []), "Pi package exports prompt shim")
    prompt_text = (ROOT / "prompts" / "feedback.md").read_text(encoding="utf-8")
    report.check("$ARGUMENTS" in prompt_text, "Pi prompt forwards arguments")
    report.check("${ARGUMENTS:-" not in prompt_text, "Pi prompt uses supported substitution syntax")


def validate_assets(report: Report) -> None:
    for rel, size in [("hero.svg", (1600, 760)), ("workflow.svg", (1440, 430)), ("loop-mark.svg", (256, 256))]:
        path = ROOT / "assets" / rel
        try:
            tree = ET.parse(path)
            viewbox = tree.getroot().attrib.get("viewBox", "")
            expected = f"0 0 {size[0]} {size[1]}"
            report.check(viewbox == expected, f"SVG dimensions: {rel}", viewbox)
        except (OSError, ET.ParseError) as exc:
            report.check(False, f"valid SVG: {rel}", str(exc))
    card = ROOT / "assets" / "social-card.png"
    try:
        report.check(png_dimensions(card) == (1280, 640), "social card dimensions", str(png_dimensions(card)))
        report.check(card.stat().st_size < 1_000_000, "social card size under 1MB", str(card.stat().st_size))
    except (OSError, ValueError, struct.error) as exc:
        report.check(False, "valid social-card PNG", str(exc))


def validate_public_surface(report: Report) -> None:
    ignored_parts = {".git", ".ruff_cache", ".pytest_cache", ".venv", "__pycache__"}
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if (
            not path.is_file()
            or any(part in ignored_parts for part in relative.parts)
            or relative.as_posix().startswith("evals/results/")
            or path.suffix.lower() in {".png", ".pyc"}
        ):
            continue
        # This validator contains the leak-detection canaries by definition.
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PRIVATE_PATTERNS.items():
            matches = [m.group(0) for m in pattern.finditer(text) if m.group(0) not in CANARY_ALLOWLIST]
            report.check(not matches, f"no {label}: {path.relative_to(ROOT)}", ", ".join(matches[:3]))


def validate_installer(report: Report) -> None:
    installer = ROOT / "scripts" / "install.py"
    try:
        compile(installer.read_text(encoding="utf-8"), str(installer), "exec")
        report.check(True, "installer compiles")
    except SyntaxError as exc:
        report.check(False, "installer compiles", str(exc))
        return
    with tempfile.TemporaryDirectory(prefix="feedback-validate-") as temp:
        home = Path(temp) / "home"
        cmd = [sys.executable, str(installer), "--target", "all", "--home", str(home)]
        first = subprocess.run(
            cmd, cwd=ROOT, text=True, capture_output=True, timeout=30, check=False
        )
        report.check(first.returncode == 0, "installer isolated all-target smoke", first.stderr or first.stdout)
        expected = [
            home / ".agents/skills/feedback/SKILL.md",
            home / ".claude/skills/feedback/SKILL.md",
            home / ".hermes/skills/feedback/SKILL.md",
            home / ".pi/agent/prompts/feedback.md",
        ]
        report.check(all(path.is_file() for path in expected), "installer writes all expected surfaces")
        second = subprocess.run(
            cmd, cwd=ROOT, text=True, capture_output=True, timeout=30, check=False
        )
        report.check(second.returncode != 0 and "Refusing to overwrite" in (second.stdout + second.stderr), "installer refuses implicit overwrite")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    args = parser.parse_args()
    report = Report()
    validate_skill(report)
    validate_markdown_links(report)
    validate_metadata(report)
    validate_assets(report)
    validate_public_surface(report)
    validate_installer(report)

    payload = {"passed": len(report.passed), "failed": len(report.failed), "failures": report.failed}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for label in report.passed:
            print(f"PASS  {label}")
        for label in report.failed:
            print(f"FAIL  {label}")
        print(f"\n{len(report.passed)} passed, {len(report.failed)} failed")
    return 1 if report.failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
