from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hooks.block_destructive_bash import find_violation, handle_payload


class DestructiveCommandHookTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked_commands = {
            "rm -rf /tmp/build": "rm -rf",
            "sudo rm -fr ./dist": "rm -rf",
            "rm --recursive --force cache": "rm -rf",
            "git push origin main --force": "git push --force",
            "git push origin main --force-with-lease=main": "git push --force",
            "git push -f origin main": "git push --force",
            "psql -c 'DROP   TABLE users'": "DROP TABLE",
            "mysql -e 'TRUNCATE sessions'": "TRUNCATE",
            "psql -c 'DELETE   FROM accounts;'": "DELETE FROM without WHERE",
        }

        for command, expected_rule in blocked_commands.items():
            with self.subTest(command=command):
                self.assertEqual(find_violation(command), expected_rule)

    def test_allows_normal_bash_commands(self) -> None:
        allowed_commands = [
            "git status --short",
            "npm test",
            "rm -r ./build",
            "psql -c 'DELETE FROM accounts WHERE id = 42;'",
            "git push origin main",
        ]

        for command in allowed_commands:
            with self.subTest(command=command):
                self.assertIsNone(find_violation(command))

    def test_denies_and_logs_pretooluse_bash_payload(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf ./build"},
            "cwd": "/workspace/project",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            response = handle_payload(payload, log_path)

            self.assertIsNotNone(response)
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])

            [record] = log_path.read_text(encoding="utf-8").splitlines()
            logged = json.loads(record)
            self.assertEqual(logged["attempted_command"], "rm -rf ./build")
            self.assertEqual(logged["project_path"], "/workspace/project")
            self.assertEqual(logged["matched_rule"], "rm -rf")

    def test_ignores_non_bash_tools(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md"},
            "cwd": "/workspace/project",
        }

        self.assertIsNone(handle_payload(payload))


if __name__ == "__main__":
    unittest.main()
