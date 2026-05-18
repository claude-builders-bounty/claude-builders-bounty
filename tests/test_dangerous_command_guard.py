import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


HOOK_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "dangerous-command-guard.py"
SPEC = importlib.util.spec_from_file_location("dangerous_command_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class DangerousCommandGuardTests(unittest.TestCase):
    def test_allows_safe_bash_command(self):
        self.assertIsNone(guard.blocked_reason("python -m pytest"))

    def test_ignores_non_bash_tool(self):
        payload = {"tool_name": "Read", "tool_input": {"command": "rm -rf build"}}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
            self.assertEqual(guard.main(), 0)

    def test_blocks_required_patterns(self):
        commands = [
            "rm -rf build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "mysql -e 'TRUNCATE users'",
            "psql -c 'DELETE FROM users'",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_allows_delete_from_with_where(self):
        self.assertIsNone(guard.blocked_reason("psql -c 'DELETE FROM users WHERE id = 1'"))

    def test_denies_and_logs_blocked_command(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf build"},
            "cwd": "/tmp/example-project",
        }

        with TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            with (
                patch.object(guard, "LOG_PATH", log_path),
                patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                redirect_stdout(io.StringIO()) as stdout,
            ):
                self.assertEqual(guard.main(), 0)

            output = json.loads(stdout.getvalue())
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["command"], "rm -rf build")
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")


if __name__ == "__main__":
    unittest.main()
