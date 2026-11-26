"""Exercise installation in disposable directories, never in the user's home."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


INSTALLER = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("guard_installer", INSTALLER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE = b"import sys\nprint('fixture hook')\nsys.exit(0)\n"


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source with spaces ' and $"
        self.source.mkdir()
        shutil.copyfile(INSTALLER, self.source / "install.py")
        (self.source / "guard.py").write_bytes(FIXTURE)
        self.claude = self.root / "config with spaces ' and $"

    def tearDown(self):
        self.temporary.cleanup()

    def run_installer(self):
        return subprocess.run(
            [sys.executable, str(self.source / "install.py"), "--claude-dir", str(self.claude)],
            capture_output=True, text=True, check=False,
        )

    def settings(self):
        return json.loads((self.claude / "settings.json").read_text())

    def write_settings(self, value):
        self.claude.mkdir(exist_ok=True)
        (self.claude / "settings.json").write_text(json.dumps(value))

    def test_fresh_install_uses_exec_arguments_for_special_paths(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        group, = self.settings()["hooks"]["PreToolUse"]
        self.assertEqual(group["matcher"], "Bash")
        handler, = group["hooks"]
        self.assertEqual(handler["type"], "command")
        self.assertEqual(handler["command"], sys.executable)
        installed = self.claude / "hooks" / "destructive_command_guard.py"
        self.assertEqual(handler["args"], [str(installed)])
        self.assertEqual(installed.read_bytes(), FIXTURE)
        invoked = subprocess.run(
            [handler["command"]] + handler["args"], capture_output=True, text=True, check=False,
        )
        self.assertEqual(invoked.returncode, 0, invoked.stderr)
        self.assertEqual(invoked.stdout, "fixture hook\n")

    def test_existing_settings_and_hooks_are_preserved_and_backed_up(self):
        existing = {
            "permissions": {"allow": ["Read"], "deny": ["Bash(curl *)"]},
            "custom": {"unicode": "配置"},
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "echo done"}]}],
                "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo existing"}]}],
            },
        }
        self.write_settings(existing)
        raw = (self.claude / "settings.json").read_bytes()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = self.settings()
        self.assertEqual(updated["permissions"], existing["permissions"])
        self.assertEqual(updated["custom"], existing["custom"])
        self.assertEqual(updated["hooks"]["Stop"], existing["hooks"]["Stop"])
        self.assertEqual(updated["hooks"]["PreToolUse"][0], existing["hooks"]["PreToolUse"][0])
        self.assertEqual((self.claude / "settings.json.bak").read_bytes(), raw)

    def test_repeated_install_is_idempotent_and_keeps_formatting(self):
        self.write_settings({"model": "test"})
        first = self.run_installer()
        self.assertEqual(first.returncode, 0, first.stderr)
        settings_path = self.claude / "settings.json"
        # A user's formatting-only edit must survive a no-op reinstall.
        reformatted = json.dumps(self.settings(), separators=(",", ":")).encode()
        settings_path.write_bytes(reformatted)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(settings_path.read_bytes(), reformatted)
        self.assertEqual(len(self.settings()["hooks"]["PreToolUse"]), 1)
        self.assertEqual(len(list(self.claude.glob("settings.json.bak*"))), 1)

    def test_reinstall_updates_script_without_duplicate_hook(self):
        self.assertEqual(self.run_installer().returncode, 0)
        changed = FIXTURE + b"# new version\n"
        (self.source / "guard.py").write_bytes(changed)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.claude / "hooks" / "destructive_command_guard.py").read_bytes(), changed)
        self.assertEqual(len(self.settings()["hooks"]["PreToolUse"]), 1)

    def test_existing_backup_is_never_overwritten(self):
        self.write_settings({"model": "test"})
        previous = b"older backup\n"
        (self.claude / "settings.json.bak").write_bytes(previous)
        original = (self.claude / "settings.json").read_bytes()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.claude / "settings.json.bak").read_bytes(), previous)
        self.assertEqual((self.claude / "settings.json.bak.1").read_bytes(), original)

    def test_malformed_json_is_rejected_without_writes(self):
        self.claude.mkdir()
        raw = b'{"hooks":\n'
        (self.claude / "settings.json").write_bytes(raw)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.claude / "settings.json").read_bytes(), raw)
        self.assertFalse((self.claude / "hooks").exists())
        self.assertFalse(list(self.claude.glob("*.bak*")))

    def test_invalid_shapes_are_rejected_without_writes(self):
        invalid = [
            [], {"hooks": None}, {"hooks": []},
            {"hooks": {"PreToolUse": {}}},
            {"hooks": {"PreToolUse": ["bad"]}},
            {"hooks": {"PreToolUse": [{"matcher": [], "hooks": []}]}},
            {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": {}}]}},
            {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [None]}]}},
        ]
        for value in invalid:
            with self.subTest(value=value):
                self.write_settings(value)
                raw = (self.claude / "settings.json").read_bytes()
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((self.claude / "settings.json").read_bytes(), raw)
                self.assertFalse((self.claude / "hooks").exists())
                self.assertFalse(list(self.claude.glob("*.bak*")))

    def test_duplicate_json_keys_are_rejected(self):
        self.claude.mkdir()
        raw = b'{"hooks": {}, "hooks": {"PreToolUse": []}}'
        (self.claude / "settings.json").write_bytes(raw)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate key", result.stderr)
        self.assertEqual((self.claude / "settings.json").read_bytes(), raw)
        self.assertFalse((self.claude / "hooks").exists())

    def test_nonstandard_json_numbers_are_rejected(self):
        self.claude.mkdir()
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                raw = ('{"timeout": ' + value + '}').encode()
                (self.claude / "settings.json").write_bytes(raw)
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((self.claude / "settings.json").read_bytes(), raw)
                self.assertFalse((self.claude / "hooks").exists())

    def test_missing_source_does_not_change_settings(self):
        self.write_settings({"model": "test"})
        raw = (self.claude / "settings.json").read_bytes()
        (self.source / "guard.py").unlink()
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.claude / "settings.json").read_bytes(), raw)
        self.assertFalse((self.claude / "hooks").exists())

    def test_settings_symlink_is_not_replaced(self):
        self.claude.mkdir()
        external = self.root / "external.json"
        external.write_text('{"model": "test"}')
        try:
            (self.claude / "settings.json").symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.claude / "settings.json").is_symlink())
        self.assertEqual(external.read_text(), '{"model": "test"}')

    def test_script_symlink_is_not_replaced(self):
        (self.claude / "hooks").mkdir(parents=True)
        external = self.root / "external.py"
        external.write_bytes(b"original script")
        target = self.claude / "hooks" / "destructive_command_guard.py"
        try:
            target.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.is_symlink())
        self.assertEqual(external.read_bytes(), b"original script")
        self.assertFalse((self.claude / "settings.json").exists())

    def test_interpreter_change_updates_existing_handler(self):
        target = self.claude / "hooks" / "destructive_command_guard.py"
        settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{
            "type": "command", "command": "/old/python", "args": [str(target)], "timeout": 5,
        }]}]}}
        merged = MODULE._merge_settings(settings, target)
        handler = merged["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(handler["command"], sys.executable)
        self.assertEqual(handler["timeout"], 5)
        self.assertEqual(settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "/old/python")

    def test_atomic_write_failure_leaves_original_and_cleans_temporary(self):
        target = self.root / "settings.json"
        target.write_bytes(b"original")
        with mock.patch.object(MODULE.os, "replace", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                MODULE._atomic_write(target, b"replacement")
        self.assertEqual(target.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob(".settings.json.*")), [])


if __name__ == "__main__":
    unittest.main()
