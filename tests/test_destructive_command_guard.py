import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive-command-guard.py"

spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DestructiveCommandGuardTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked_commands = [
            "rm -rf build",
            "sudo rm -fr /tmp/example",
            "git push origin main --force",
            "git push origin main -f",
            "git push --force-with-lease origin main",
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'TRUNCATE sessions'",
            "mysql -e 'DELETE FROM users'",
        ]

        for command in blocked_commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.find_block_reason(command))

    def test_allows_non_destructive_commands(self):
        allowed_commands = [
            "rm build.log",
            "git push origin main",
            "pytest",
            "sqlite3 app.db 'DELETE FROM sessions WHERE id = 1'",
            "psql -c 'SELECT * FROM users'",
        ]

        for command in allowed_commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.find_block_reason(command))

    def test_denial_output_and_log(self):
        payload = {
            "tool_name": "Bash",
            "cwd": "/workspace/example",
            "tool_input": {"command": "rm -rf dist"},
        }

        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )

            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["command"], "rm -rf dist")
            self.assertEqual(log_entry["attempted_command"], "rm -rf dist")
            self.assertEqual(log_entry["project_path"], "/workspace/example")
            self.assertIn("timestamp", log_entry)

    def test_normal_command_is_silent(self):
        payload = {
            "tool_name": "Bash",
            "cwd": "/workspace/example",
            "tool_input": {"command": "npm test"},
        }

        with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))):
            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(guard.main(), 0)
                self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
