#!/usr/bin/env python3
"""Tests for the destructive Bash guard hook."""

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))

from block_destructive_bash import detect_dangerous_command  # noqa: E402


class DestructiveBashGuardTest(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        commands = [
            "rm -rf build",
            "DROP TABLE users",
            "git push origin main --force",
            "TRUNCATE audit_log",
            "psql -c 'DELETE FROM users'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(detect_dangerous_command(command))

    def test_allows_normal_commands(self) -> None:
        commands = [
            "ls -la",
            "rm -r build",
            "git push origin main",
            "python -m pytest",
            "psql -c 'DELETE FROM users WHERE id = 1'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(detect_dangerous_command(command))


if __name__ == "__main__":
    unittest.main()
