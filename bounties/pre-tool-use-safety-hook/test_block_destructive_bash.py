#!/usr/bin/env python3
"""Small local tests for block_destructive_bash.py."""

from __future__ import annotations

import unittest

from block_destructive_bash import blocked_reason


class SafetyHookTests(unittest.TestCase):
    def test_blocks_rm_rf(self) -> None:
        self.assertIsNotNone(blocked_reason("rm -rf ./dist"))
        self.assertIsNotNone(blocked_reason("sudo rm -fr /tmp/example"))

    def test_blocks_force_push(self) -> None:
        self.assertIsNotNone(blocked_reason("git push --force origin main"))
        self.assertIsNotNone(blocked_reason("git push -f"))

    def test_blocks_destructive_sql(self) -> None:
        self.assertIsNotNone(blocked_reason("DROP TABLE users;"))
        self.assertIsNotNone(blocked_reason("TRUNCATE audit_log;"))
        self.assertIsNotNone(blocked_reason("DELETE FROM users;"))

    def test_allows_delete_with_where(self) -> None:
        self.assertIsNone(blocked_reason("DELETE FROM users WHERE id = 1;"))

    def test_allows_normal_commands(self) -> None:
        self.assertIsNone(blocked_reason("git status --short"))
        self.assertIsNone(blocked_reason("python -m pytest"))
        self.assertIsNone(blocked_reason("rm ./single-file.tmp"))


if __name__ == "__main__":
    unittest.main()
