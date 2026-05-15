import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre-tool-use" / "destructive_command_guard.py"
spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class DestructiveCommandGuardTest(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked = [
            "rm -rf build",
            "sudo rm -fr /tmp/example",
            "psql -c 'DROP TABLE users'",
            "TRUNCATE audit_log",
            "git push origin main --force",
            "git push -f origin main",
            "DELETE FROM users",
            "DELETE FROM users WHERE id = 1; DELETE FROM sessions",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_allows_safe_commands(self):
        allowed = [
            "ls -la",
            "rm -r build",
            "git push origin main",
            "git push --force-with-lease-preview",
            "SELECT * FROM users",
            "DELETE FROM users WHERE id = 1",
            "echo 'DROP TABLE is documented here'",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command))

    def test_extracts_claude_hook_payload_fields(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force", "cwd": "/repo"},
        }
        self.assertEqual(guard.extract_command(payload), "git push --force")
        self.assertEqual(guard.extract_project_path(payload), "/repo")
        self.assertTrue(guard.is_bash_tool(payload, "git push --force"))

    def test_non_bash_tool_is_ignored(self):
        payload = {
            "tool_name": "Read",
            "tool_input": {"command": "rm -rf build", "cwd": "/repo"},
        }
        self.assertFalse(guard.is_bash_tool(payload, "rm -rf build"))

    def test_blocked_attempt_is_logged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            with mock.patch.object(guard, "LOG_PATH", log_path):
                guard.log_blocked("rm -rf build", "/repo", "rm -rf")

            contents = log_path.read_text(encoding="utf-8")
            self.assertIn('"command": "rm -rf build"', contents)
            self.assertIn('"project_path": "/repo"', contents)
            self.assertIn('"pattern": "rm -rf"', contents)
            self.assertIn('"timestamp":', contents)


if __name__ == "__main__":
    unittest.main()
