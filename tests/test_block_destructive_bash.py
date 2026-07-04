from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from support import load_hook_module


hook = load_hook_module()


class BlockDestructiveBashTests(unittest.TestCase):
    def test_blocks_required_destructive_patterns(self) -> None:
        commands = [
            "rm -rf dist",
            "rm -fr build",
            "git push origin main --force",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM users'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.find_block_reason(command))

    def test_allows_safe_commands(self) -> None:
        commands = [
            "rm -r dist",
            "git push origin main",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "pytest tests/test_block_destructive_bash.py",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(hook.find_block_reason(command))

    def test_evaluate_logs_blocked_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            blocked, message = hook.evaluate(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf /tmp/example"},
                    "cwd": "/repo",
                },
                log_path,
            )

            self.assertTrue(blocked)
            self.assertIn("Blocked destructive Bash command", message)

            [line] = log_path.read_text(encoding="utf-8").splitlines()
            record = json.loads(line)
            self.assertEqual(record["attempted_command"], "rm -rf /tmp/example")
            self.assertEqual(record["project_path"], "/repo")
            self.assertIn("timestamp", record)

    def test_ignores_non_bash_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            blocked, message = hook.evaluate(
                {
                    "tool_name": "Read",
                    "tool_input": {"command": "rm -rf /tmp/example"},
                    "cwd": "/repo",
                },
                log_path,
            )

            self.assertFalse(blocked)
            self.assertEqual(message, "")
            self.assertFalse(log_path.exists())


if __name__ == "__main__":
    unittest.main()
