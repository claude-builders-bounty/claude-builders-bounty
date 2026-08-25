#!/usr/bin/env python3
"""Unit tests for block_destructive hook."""

import unittest

from block_destructive import match_blocked


class TestBlockDestructive(unittest.TestCase):
    def test_blocks_rm_rf(self) -> None:
        self.assertEqual(match_blocked("rm -rf /tmp/data"), "rm -rf")
        self.assertEqual(match_blocked("rm -fr build/"), "rm -rf")

    def test_blocks_drop_table(self) -> None:
        self.assertEqual(match_blocked("DROP TABLE users;"), "DROP TABLE")

    def test_blocks_git_force_push(self) -> None:
        self.assertEqual(
            match_blocked("git push origin main --force"), "git push --force"
        )
        self.assertEqual(match_blocked("git push -f origin main"), "git push --force")

    def test_blocks_truncate(self) -> None:
        self.assertEqual(match_blocked("TRUNCATE TABLE logs"), "TRUNCATE")

    def test_blocks_delete_without_where(self) -> None:
        self.assertEqual(match_blocked("DELETE FROM customers"), "DELETE FROM without WHERE")
        self.assertEqual(match_blocked("DELETE FROM customers;"), "DELETE FROM without WHERE")

    def test_allows_safe_commands(self) -> None:
        safe = [
            "ls -la",
            "git status",
            "git push origin feature-branch",
            "npm test",
            "SELECT * FROM users WHERE id = 1",
            "DELETE FROM sessions WHERE expired_at < NOW()",
            "rm file.txt",
        ]
        for cmd in safe:
            self.assertIsNone(match_blocked(cmd), msg=cmd)


if __name__ == "__main__":
    unittest.main()
