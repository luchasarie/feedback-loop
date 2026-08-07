#!/usr/bin/env python3
"""Safe local installer for Feedback Loop.

No network calls. Existing installs are refused unless --force is explicit.
A forced replacement is moved to a timestamped sibling backup first.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = REPO_ROOT / "skills" / "feedback"
PI_PROMPT_SOURCE = REPO_ROOT / "prompts" / "feedback.md"


@dataclass(frozen=True)
class CopyPlan:
    source: Path
    destination: Path
    label: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Feedback Loop into one or more local agent clients."
    )
    parser.add_argument(
        "--target",
        choices=("all", "agents", "claude", "codex", "pi", "hermes"),
        default="all",
        help="Client target. 'agents' is the shared Codex/Pi Agent Skills location.",
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="Install into the user home or a project directory.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=None,
        help="Override the user home. Useful for isolated tests.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project directory when --scope project is used.",
    )
    parser.add_argument("--force", action="store_true", help="Back up and replace existing targets.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing files.")
    return parser.parse_args()


def target_plans(args: argparse.Namespace) -> list[CopyPlan]:
    home = (args.home or Path.home()).expanduser().resolve()
    project = args.project_root.expanduser().resolve()
    base = home if args.scope == "user" else project
    configured_hermes_home = os.environ.get("HERMES_HOME") if args.home is None else None
    hermes_root = (
        Path(configured_hermes_home).expanduser().resolve()
        if configured_hermes_home
        else home / ".hermes"
    )
    wanted = {args.target} if args.target != "all" else {"agents", "claude", "pi", "hermes"}
    plans: list[CopyPlan] = []

    if wanted & {"agents", "codex", "pi"}:
        plans.append(CopyPlan(SKILL_SOURCE, base / ".agents" / "skills" / "feedback", "shared Agent Skills"))

    if "claude" in wanted:
        plans.append(CopyPlan(SKILL_SOURCE, base / ".claude" / "skills" / "feedback", "Claude Code skill"))

    if "pi" in wanted:
        prompt_root = (home / ".pi" / "agent" / "prompts") if args.scope == "user" else (project / ".pi" / "prompts")
        plans.append(CopyPlan(PI_PROMPT_SOURCE, prompt_root / "feedback.md", "Pi /feedback prompt"))

    if "hermes" in wanted:
        if args.scope == "project":
            if args.target == "hermes":
                raise SystemExit("Hermes installation is user-scoped; use --scope user for --target hermes.")
        else:
            plans.append(CopyPlan(SKILL_SOURCE, hermes_root / "skills" / "feedback", "Hermes skill"))

    deduped: list[CopyPlan] = []
    seen: set[Path] = set()
    for plan in plans:
        if plan.destination not in seen:
            deduped.append(plan)
            seen.add(plan.destination)
    return deduped


def backup_path(destination: Path, stamp: str) -> Path:
    candidate = destination.with_name(f"{destination.name}.bak-{stamp}")
    index = 1
    while path_lexists(candidate):
        candidate = destination.with_name(f"{destination.name}.bak-{stamp}-{index}")
        index += 1
    return candidate


def path_lexists(path: Path) -> bool:
    """Return True for files, directories, and broken symlinks."""
    return path.exists() or path.is_symlink()


def copy_to_staging(plan: CopyPlan, staging: Path) -> None:
    staging.parent.mkdir(parents=True, exist_ok=True)
    if plan.source.is_dir():
        shutil.copytree(plan.source, staging)
    else:
        staging.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan.source, staging)


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path_lexists(path):
        path.unlink()


def rollback_committed(committed: list[tuple[CopyPlan, Path | None]]) -> list[str]:
    errors: list[str] = []
    for plan, backup in reversed(committed):
        destination = plan.destination
        try:
            remove_path(destination)
            if backup and path_lexists(backup):
                backup.rename(destination)
        except OSError as exc:  # best-effort rollback must continue across targets
            errors.append(f"{destination}: {exc}")
    return errors


def execute_plans(plans: list[CopyPlan], stamp: str) -> list[tuple[CopyPlan, Path | None]]:
    committed: list[tuple[CopyPlan, Path | None]] = []
    for index, plan in enumerate(plans):
        destination = plan.destination
        staging = destination.with_name(f".{destination.name}.install-{os.getpid()}-{index}")
        backup: Path | None = None
        try:
            if path_lexists(staging):
                raise RuntimeError(f"Unexpected staging path exists: {staging}")
            copy_to_staging(plan, staging)
            if path_lexists(destination):
                backup = backup_path(destination, stamp)
                destination.rename(backup)
            staging.rename(destination)
            committed.append((plan, backup))
        except Exception as install_error:
            recovery_errors: list[str] = []
            try:
                remove_path(staging)
            except OSError as exc:
                recovery_errors.append(f"staging cleanup {staging}: {exc}")
            if backup and path_lexists(backup):
                try:
                    if path_lexists(destination):
                        recovery_errors.append(
                            f"destination unexpectedly exists; preserved backup at {backup}"
                        )
                    else:
                        backup.rename(destination)
                except OSError as exc:
                    recovery_errors.append(f"current-target restore {destination}: {exc}")
            recovery_errors.extend(rollback_committed(committed))
            if recovery_errors:
                rendered = "; ".join(recovery_errors)
                raise RuntimeError(
                    f"Installation failed and rollback was incomplete: {rendered}"
                ) from install_error
            raise
    return committed


def main() -> int:
    args = parse_args()
    plans = target_plans(args)

    for plan in plans:
        if not plan.source.exists():
            raise SystemExit(f"Missing package source: {plan.source}")

    conflicts = [p.destination for p in plans if path_lexists(p.destination)]
    if conflicts and not args.force:
        rendered = "\n".join(f"  - {path}" for path in conflicts)
        raise SystemExit(
            "Refusing to overwrite existing installation(s):\n"
            f"{rendered}\n"
            "Re-run with --force to create timestamped backups first."
        )

    print(f"Feedback Loop install plan ({args.scope} scope):")
    for plan in plans:
        action = "replace with backup" if path_lexists(plan.destination) else "install"
        print(f"  - {plan.label}: {action} -> {plan.destination}")

    if args.dry_run:
        print("Dry run: no files changed.")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    committed = execute_plans(plans, stamp)

    print("Installed:")
    for plan, backup in committed:
        suffix = f" (backup: {backup})" if backup else ""
        print(f"  - {plan.destination}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
