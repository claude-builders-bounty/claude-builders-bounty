"""Installer regressions run only against temporary repositories and HOME dirs."""

import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / "install.py"


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="hook installer ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "test user's home"
        self.home.mkdir()
        self.repo = self.root / "local repository"
        (self.repo / "hooks").mkdir(parents=True)
        shutil.copyfile(INSTALLER, self.repo / "install.py")
        self.source = b"# Fixture only; no commands are executed.\n"
        (self.repo / "hooks" / "block_destructive_commands.py").write_bytes(self.source)
        self.claude = self.home / ".claude"
        self.settings_path = self.claude / "settings.json"

    def run_installer(self):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        # Running the installer never executes the installed hook.
        return subprocess.run([sys.executable, str(self.repo / "install.py")],
                              env=env, capture_output=True, text=True, timeout=10)

    def seed(self, value):
        self.claude.mkdir(exist_ok=True)
        self.settings_path.write_text(json.dumps(value), encoding="utf-8")
        return self.settings_path.read_bytes()

    def test_fresh_install_private_files_and_safely_quoted_paths(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        installed = self.claude / "hooks" / "block_destructive_commands.py"
        self.assertEqual(installed.read_bytes(), self.source)
        settings = json.loads(self.settings_path.read_text())
        entry = settings["hooks"]["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "Bash")
        self.assertEqual(entry["hooks"][0]["type"], "command")
        self.assertEqual(shlex.split(entry["hooks"][0]["command"]),
                         [sys.executable, str(installed)])
        for path in (installed, self.settings_path):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        for path in (self.claude, self.claude / "hooks"):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)

    def test_preserves_existing_settings_and_creates_exact_private_backup(self):
        existing = {"permissions": {"allow": ["Read"]}, "model": "test",
                    "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "true"}]}],
                              "PreToolUse": [{"matcher": "Bash", "hooks": [
                                  {"type": "command", "command": "echo existing"}]}]}}
        original = self.seed(existing)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(self.settings_path.read_text())
        self.assertEqual(actual["model"], existing["model"])
        self.assertEqual(actual["permissions"], existing["permissions"])
        self.assertEqual(actual["hooks"]["Stop"], existing["hooks"]["Stop"])
        self.assertEqual(actual["hooks"]["PreToolUse"][:-1], existing["hooks"]["PreToolUse"])
        backups = list(self.claude.glob("settings.json.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertEqual(stat.S_IMODE(backups[0].stat().st_mode), 0o600)

    def test_repeat_install_does_not_duplicate_hooks_or_backups(self):
        self.seed({"theme": "dark"})
        first = self.run_installer()
        self.assertEqual(first.returncode, 0, first.stderr)
        original = self.settings_path.read_bytes()
        second = self.run_installer()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.settings_path.read_bytes(), original)
        self.assertEqual(len(list(self.claude.glob("settings.json.backup-*"))), 1)
        self.assertEqual(len(json.loads(original)["hooks"]["PreToolUse"]), 1)
        self.assertFalse(list(self.claude.glob(".*.tmp")))

    def test_rejects_invalid_json_without_overwriting(self):
        self.claude.mkdir()
        original = b'{"hooks": invalid}'
        self.settings_path.write_bytes(original)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("valid UTF-8 JSON", result.stderr)
        self.assertEqual(self.settings_path.read_bytes(), original)
        self.assertFalse((self.claude / "hooks").exists())
        self.assertFalse(list(self.claude.glob("settings.json.backup-*")))

    def test_rejects_malformed_settings_structures_without_overwriting(self):
        for value in ([], {"hooks": []}, {"hooks": {"PreToolUse": {}}},
                      {"hooks": {"PreToolUse": ["wrong"]}},
                      {"hooks": {"PreToolUse": [{"hooks": ["wrong"]}]}}):
            with self.subTest(value=value):
                original = self.seed(value)
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.settings_path.read_bytes(), original)

    def test_rejects_duplicate_json_keys(self):
        self.claude.mkdir()
        original = b'{"hooks": {}, "hooks": {}}'
        self.settings_path.write_bytes(original)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate settings key", result.stderr)
        self.assertEqual(self.settings_path.read_bytes(), original)

    def test_rejects_nonstandard_json_constants(self):
        self.claude.mkdir()
        original = b'{"unrelated": NaN}'
        self.settings_path.write_bytes(original)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Non-standard JSON constant", result.stderr)
        self.assertEqual(self.settings_path.read_bytes(), original)

    def test_rejects_symlink_settings_without_touching_target(self):
        self.claude.mkdir()
        target = self.root / "outside-settings.json"
        target.write_bytes(b"{}")
        self.settings_path.symlink_to(target)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.settings_path.is_symlink())
        self.assertEqual(target.read_bytes(), b"{}")

    def test_rejects_symlink_claude_directory(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.claude.symlink_to(outside, target_is_directory=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_symlink_hooks_directory(self):
        original = self.seed({})
        outside = self.root / "outside"
        outside.mkdir()
        (self.claude / "hooks").symlink_to(outside, target_is_directory=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(self.settings_path.read_bytes(), original)

    def test_rejects_symlink_installed_script(self):
        original = self.seed({})
        (self.claude / "hooks").mkdir()
        target = self.root / "outside.py"
        target.write_bytes(b"# unchanged\n")
        (self.claude / "hooks" / "block_destructive_commands.py").symlink_to(target)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_bytes(), b"# unchanged\n")
        self.assertEqual(self.settings_path.read_bytes(), original)

    def test_rejects_nonregular_settings_without_waiting_on_fifo(self):
        self.claude.mkdir()
        os.mkfifo(self.settings_path)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(stat.S_ISFIFO(self.settings_path.lstat().st_mode))

    def test_missing_source_fails_before_creating_claude_directory(self):
        (self.repo / "hooks" / "block_destructive_commands.py").unlink()
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.claude.exists())


if __name__ == "__main__":
    unittest.main()
