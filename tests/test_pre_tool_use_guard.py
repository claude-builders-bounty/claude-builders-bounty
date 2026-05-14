import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hooks import pre_tool_use_guard as guard


class PreToolUseGuardTests(unittest.TestCase):
    def test_blocks_required_destructive_patterns(self):
        cases = [
            ("rm -rf build", "recursive-force-remove"),
            ("psql -c 'DROP TABLE users'", "drop-table"),
            ("git push --force origin main", "force-push"),
            ("sqlite3 app.db 'TRUNCATE audit_log'", "truncate"),
            ("sqlite3 app.db 'DELETE FROM users'", "delete-without-where"),
        ]
        for command, rule in cases:
            with self.subTest(command=command):
                result = guard.find_block_reason(command)
                self.assertIsNotNone(result)
                self.assertEqual(result[0], rule)

    def test_allows_normal_commands_and_safe_delete(self):
        allowed = [
            "git status --short",
            "python3 -m unittest discover -v",
            "sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP'",
            "rm -r build",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.find_block_reason(command))

    def test_extracts_claude_hook_payload_fields(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status", "cwd": "/repo"},
        }
        self.assertEqual(guard.extract_tool_name(payload), "Bash")
        self.assertEqual(guard.extract_command(payload), "git status")
        self.assertEqual(guard.extract_project_path(payload), "/repo")

    def test_cli_blocks_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git push --force origin main", "cwd": "/tmp/project"},
            }
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [sys.executable, "hooks/pre_tool_use_guard.py"],
                cwd=Path(__file__).resolve().parents[1],
                input=json.dumps(payload),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("blocked this Bash command", result.stderr)
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_line = log_path.read_text()
            self.assertIn("force-push", log_line)
            self.assertIn("/tmp/project", log_line)


if __name__ == "__main__":
    unittest.main()
