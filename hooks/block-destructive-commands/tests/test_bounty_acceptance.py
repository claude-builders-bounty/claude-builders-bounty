#!/usr/bin/env python3
"""Explicit bounty #3 acceptance criteria regression tests."""

import importlib.util
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "pre-tool-use.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BountyAcceptanceTests(unittest.TestCase):
    """Maps directly to issue #3 acceptance criteria."""

    @classmethod
    def setUpClass(cls):
        cls.hook = load_hook_module()

    def test_blocks_required_destructive_patterns(self):
        blocked = (
            ("rm -rf /tmp", "Recursive force delete (rm -rf)"),
            ("rm --force --recursive /tmp", "Recursive force delete (rm -rf)"),
            ("DROP TABLE users", "SQL DROP TABLE"),
            ("git push --force origin main", "Git force push (git push --force)"),
            ("TRUNCATE sessions", "SQL TRUNCATE"),
            ("DELETE FROM users", "SQL DELETE FROM without WHERE clause"),
        )
        for command, reason in blocked:
            with self.subTest(command=command):
                self.assertEqual(self.hook.check_command(command), reason)

    def test_allows_safe_command_variants(self):
        allowed = (
            "git status",
            "rm -f README.md",
            "git push --force-with-lease origin main",
            "git push --force-if-includes origin main",
            "DELETE FROM users WHERE id = 1",
            "npm run truncate-logs",
            "npm run drop-table-migration",
            'grep "DELETE FROM users" schema.sql',
            "echo DROP TABLE users",
        )
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(self.hook.check_command(command))

    def test_blocks_sql_in_shell_c_wrappers(self):
        blocked = (
            "sh -c 'DROP TABLE users'",
            'bash -c "DELETE FROM sessions"',
            r"bash -c $'DROP\x20TABLE\x20users'",
        )
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(self.hook.check_command(command))

    def test_blocks_rm_in_shell_c_with_intervening_flags(self):
        blocked = (
            'bash --login -c "rm -rf /"',
            'bash --login --posix -c "rm -rf /"',
            'bash -l -c "rm -rf /"',
            'bash -lc "rm -rf /tmp"',
            'sh --login -c "rm -rf /data"',
            'zsh -lc "rm -rf /var/tmp"',
            'env bash -lc "rm -rf /srv"',
        )
        for command in blocked:
            with self.subTest(command=command):
                self.assertEqual(
                    self.hook.check_command(command),
                    "Recursive force delete (rm -rf)",
                )


if __name__ == "__main__":
    unittest.main()
