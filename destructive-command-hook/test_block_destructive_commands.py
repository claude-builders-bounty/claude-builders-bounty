#!/usr/bin/env python3
import unittest

from block_destructive_commands import block_reason


class BlockDestructiveCommandsTest(unittest.TestCase):
    def assert_blocked(self, command: str) -> None:
        self.assertIsNotNone(block_reason(command), command)

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(block_reason(command), command)

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf build")
        self.assert_blocked("sudo rm -fr /tmp/example")

    def test_blocks_sql_destructive_commands(self) -> None:
        self.assert_blocked("DROP TABLE users")
        self.assert_blocked("truncate table sessions")
        self.assert_blocked("DELETE FROM users")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main")

    def test_allows_safe_commands(self) -> None:
        self.assert_allowed("rm build.log")
        self.assert_allowed("git push origin main")
        self.assert_allowed("DELETE FROM users WHERE id = 1")
        self.assert_allowed("python3 -m pytest")


if __name__ == "__main__":
    unittest.main()
