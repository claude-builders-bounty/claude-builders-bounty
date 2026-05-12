import json
import os
import tempfile
import unittest
from pathlib import Path

from hooks.block_destructive_bash import (
    build_decision,
    extract_command,
    find_block_reason,
    write_block_log,
)


class BlockDestructiveBashTests(unittest.TestCase):
    def test_extracts_bash_command_from_claude_pre_tool_use_input(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "npm test"}}

        self.assertEqual(extract_command(payload), "npm test")

    def test_blocks_required_destructive_patterns(self):
        cases = [
            ("rm -rf /tmp/build", "rm -rf"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push --force origin main", "git push --force"),
            ("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE"),
            ("psql -c 'DELETE FROM users'", "DELETE FROM without WHERE"),
        ]

        for command, expected_reason in cases:
            with self.subTest(command=command):
                self.assertIn(expected_reason, find_block_reason(command))

    def test_allows_normal_commands_and_delete_with_where_clause(self):
        allowed = [
            "npm test",
            "git push origin feature/safe-branch",
            "python manage.py migrate",
            "psql -c 'DELETE FROM sessions WHERE expires_at < now()'",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(find_block_reason(command))

    def test_build_decision_matches_claude_code_pre_tool_use_schema(self):
        decision = build_decision("rm -rf /", "rm -rf")

        self.assertEqual(
            decision,
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Blocked destructive Bash command: rm -rf. Command was not executed.",
                }
            },
        )
        json.dumps(decision)

    def test_writes_blocked_attempt_log_with_timestamp_command_and_project_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            write_block_log(log_path, "rm -rf /tmp/build", "/repo/project")

            line = log_path.read_text(encoding="utf-8").strip()
            self.assertIn("command=rm -rf /tmp/build", line)
            self.assertIn("project_path=/repo/project", line)
            self.assertRegex(line, r"^\d{4}-\d{2}-\d{2}T")


if __name__ == "__main__":
    unittest.main()
