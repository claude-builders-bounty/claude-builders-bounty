import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".install-test-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.config = self.work / "config with 'quote' and spaces"
        self.config.mkdir()
        self.settings = self.config / "settings.json"

    def install(self):
        return subprocess.run(
            [sys.executable, str(ROOT / "install.py"), "--config-dir", str(self.config)],
            capture_output=True, text=True, timeout=5,
        )

    def test_preserves_existing_configuration_and_is_idempotent(self):
        old_handler = {"type": "command", "command": "echo existing-hook"}
        original = {"model": "preserve-me", "permissions": {"deny": ["Read(.env)"]},
                    "hooks": {"PostToolUse": [{"matcher": "Write", "hooks": [old_handler]}],
                              "PreToolUse": [{"matcher": "Bash", "hooks": [old_handler]}]}}
        original_bytes = json.dumps(original).encode()
        self.settings.write_bytes(original_bytes)
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        installed = json.loads(self.settings.read_text())
        self.assertEqual(installed["model"], original["model"])
        self.assertEqual(installed["permissions"], original["permissions"])
        self.assertEqual(installed["hooks"]["PostToolUse"], original["hooks"]["PostToolUse"])
        self.assertEqual(installed["hooks"]["PreToolUse"][0], original["hooks"]["PreToolUse"][0])
        self.assertEqual(len(installed["hooks"]["PreToolUse"]), 2)
        backup = self.config / "settings.json.before-destructive-guard"
        self.assertEqual(backup.read_bytes(), original_bytes)
        first = self.settings.read_bytes()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.settings.read_bytes(), first)
        self.assertEqual(backup.read_bytes(), original_bytes)

    def test_registered_command_runs_with_spaces_and_quotes_in_paths(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        handler = json.loads(self.settings.read_text())["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(handler["type"], "command")
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "cwd": str(self.work / "project"),
                 "tool_input": {"command": "git push --force"}}
        # Execute only the installer-generated Python launcher, never tool_input.command.
        result = subprocess.run(["/bin/sh", "-c", handler["command"]],
                                input=json.dumps(event), capture_output=True,
                                text=True, timeout=5, cwd=self.work)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]
                         ["permissionDecision"], "deny")
        record = json.loads((self.config / "hooks" / "blocked.log").read_text())
        self.assertEqual(record["cwd"], event["cwd"])
        self.assertEqual(record["command"], event["tool_input"]["command"])
        self.assertEqual((self.config / "hooks" / "destructive-command-guard.py").read_bytes(),
                         (ROOT / "guard.py").read_bytes())

    def test_invalid_settings_are_not_overwritten(self):
        for content in ["{invalid", "[]", '{"hooks": []}',
                        '{"hooks": {"PreToolUse": {}}}',
                        '{"hooks": {"PreToolUse": [{"hooks": [1]}]}}']:
            with self.subTest(content=content):
                self.settings.write_text(content)
                result = self.install()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.settings.read_text(), content)
                self.assertFalse((self.config / "hooks").exists())

    def test_symbolic_link_settings_are_not_replaced(self):
        original = self.work / "external-settings.json"
        original.write_text('{"model": "keep"}')
        self.settings.symlink_to(original)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.settings.is_symlink())
        self.assertEqual(original.read_text(), '{"model": "keep"}')

    def test_symbolic_link_script_is_not_replaced(self):
        original = self.work / "external-script.py"
        original.write_text("# keep this file\n")
        hooks = self.config / "hooks"
        hooks.mkdir()
        (hooks / "destructive-command-guard.py").symlink_to(original)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(original.read_text(), "# keep this file\n")
        self.assertFalse(self.settings.exists())


if __name__ == "__main__":
    unittest.main()
