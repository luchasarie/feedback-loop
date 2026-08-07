from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("feedback_installer", ROOT / "scripts" / "install.py")
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def plan(self, source: Path, destination: Path, label: str = "test"):
        return installer.CopyPlan(source, destination, label)

    def test_successful_replacement_preserves_timestamped_backup(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source"
            destination = root / "feedback"
            source.mkdir()
            destination.mkdir()
            (source / "value.txt").write_text("new", encoding="utf-8")
            (destination / "value.txt").write_text("old", encoding="utf-8")

            committed = installer.execute_plans([self.plan(source, destination)], "STAMP")

            self.assertEqual((destination / "value.txt").read_text(), "new")
            backup = committed[0][1]
            self.assertEqual(backup, root / "feedback.bak-STAMP")
            self.assertEqual((backup / "value.txt").read_text(), "old")

    def test_staging_rename_failure_restores_current_and_prior_targets(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sources = []
            destinations = []
            for index in (1, 2):
                source = root / f"source{index}"
                destination = root / f"dest{index}"
                source.mkdir()
                destination.mkdir()
                (source / "value.txt").write_text(f"new{index}", encoding="utf-8")
                (destination / "value.txt").write_text(f"old{index}", encoding="utf-8")
                sources.append(source)
                destinations.append(destination)

            original_rename = Path.rename

            def rename_with_failure(path: Path, target: Path):
                if path.name == f".dest2.install-{os.getpid()}-1":
                    raise OSError("injected staging rename failure")
                return original_rename(path, target)

            with (
                mock.patch.object(Path, "rename", rename_with_failure),
                self.assertRaisesRegex(OSError, "injected staging rename failure"),
            ):
                installer.execute_plans(
                    [self.plan(sources[0], destinations[0]), self.plan(sources[1], destinations[1])],
                    "STAMP",
                )

            self.assertEqual((destinations[0] / "value.txt").read_text(), "old1")
            self.assertEqual((destinations[1] / "value.txt").read_text(), "old2")
            self.assertFalse(any(root.glob("*.bak-*")))
            self.assertFalse(any(root.glob(".*.install-*")))

    def test_partial_copy_failure_cleans_staging_and_rolls_back_prior_install(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source1 = root / "source1"
            source2 = root / "source2"
            source1.mkdir()
            source2.mkdir()
            (source1 / "value.txt").write_text("new1", encoding="utf-8")
            (source2 / "value.txt").write_text("new2", encoding="utf-8")
            destination1 = root / "dest1"
            destination2 = root / "dest2"
            destination2.mkdir()
            (destination2 / "value.txt").write_text("old2", encoding="utf-8")
            original_copy = installer.copy_to_staging

            def copy_with_failure(plan, staging):
                if plan.destination == destination2:
                    staging.mkdir(parents=True)
                    (staging / "partial.txt").write_text("partial", encoding="utf-8")
                    raise OSError("injected copy failure")
                return original_copy(plan, staging)

            with (
                mock.patch.object(installer, "copy_to_staging", copy_with_failure),
                self.assertRaisesRegex(OSError, "injected copy failure"),
            ):
                installer.execute_plans(
                    [self.plan(source1, destination1), self.plan(source2, destination2)],
                    "STAMP",
                )

            self.assertFalse(destination1.exists())
            self.assertEqual((destination2 / "value.txt").read_text(), "old2")
            self.assertFalse(any(root.glob(".*.install-*")))

    def test_remove_path_unlinks_symlink_without_deleting_target(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "target"
            target.mkdir()
            (target / "keep.txt").write_text("keep", encoding="utf-8")
            link = root / "link"
            link.symlink_to(target, target_is_directory=True)

            installer.remove_path(link)

            self.assertFalse(link.exists())
            self.assertEqual((target / "keep.txt").read_text(), "keep")

    def test_project_all_skips_user_scoped_hermes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args = argparse.Namespace(
                target="all",
                scope="project",
                home=root / "home",
                project_root=root / "project",
            )
            destinations = {plan.destination for plan in installer.target_plans(args)}
            self.assertIn((root / "project/.agents/skills/feedback").resolve(), destinations)
            self.assertIn((root / "project/.claude/skills/feedback").resolve(), destinations)
            self.assertIn((root / "project/.pi/prompts/feedback.md").resolve(), destinations)
            self.assertFalse(any(".hermes" in str(path) for path in destinations))

    def test_explicit_project_hermes_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args = argparse.Namespace(
                target="hermes",
                scope="project",
                home=root / "home",
                project_root=root / "project",
            )
            with self.assertRaisesRegex(SystemExit, "user-scoped"):
                installer.target_plans(args)

    def test_backup_path_uses_collision_suffix(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            destination = root / "feedback"
            (root / "feedback.bak-STAMP").mkdir()
            self.assertEqual(
                installer.backup_path(destination, "STAMP"),
                root / "feedback.bak-STAMP-1",
            )

    def test_broken_symlink_is_refused_without_force(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            destination = home / ".agents/skills/feedback"
            destination.parent.mkdir(parents=True)
            destination.symlink_to(root / "missing-target", target_is_directory=True)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/install.py"),
                    "--target",
                    "agents",
                    "--home",
                    str(home),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Refusing to overwrite", completed.stdout + completed.stderr)
            self.assertTrue(destination.is_symlink())
            self.assertFalse(any(destination.parent.glob("feedback.bak-*")))

    def test_hermes_target_respects_configured_hermes_home(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            configured = root / "custom-hermes"
            args = argparse.Namespace(
                target="hermes",
                scope="user",
                home=None,
                project_root=root / "project",
            )
            with mock.patch.dict(os.environ, {"HERMES_HOME": str(configured)}):
                plans = installer.target_plans(args)
            self.assertEqual(plans[0].destination, configured / "skills/feedback")

    def test_explicit_home_overrides_configured_hermes_home(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            explicit = root / "explicit-user"
            args = argparse.Namespace(
                target="hermes",
                scope="user",
                home=explicit,
                project_root=root / "project",
            )
            with mock.patch.dict(os.environ, {"HERMES_HOME": str(root / "ignored")}):
                plans = installer.target_plans(args)
            self.assertEqual(plans[0].destination, explicit.resolve() / ".hermes/skills/feedback")


if __name__ == "__main__":
    unittest.main()
