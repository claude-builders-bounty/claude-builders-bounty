#!/usr/bin/env python3
"""
Unit tests for Claude Code Pre-Tool-Use Safety Hook
"""

import unittest
from pre_tool_use_safety_hook import check_command

class TestSafetyHook(unittest.TestCase):

    def test_blocks_rm_rf(self):
        blocked_cmds = [
            "rm -rf /tmp/data",
            "rm -fr /home/user",
            "rm -r -f build/",
            "rm -f -r cache/"
        ]
        for cmd in blocked_cmds:
            allowed, reason = check_command(cmd)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked")
            self.assertIn("rm -rf", reason)

    def test_blocks_git_force_push(self):
        blocked_cmds = [
            "git push origin main --force",
            "git push --force origin main",
            "git push -f",
            "git push origin release/v1 -f"
        ]
        for cmd in blocked_cmds:
            allowed, reason = check_command(cmd)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked")
            self.assertIn("force", reason.lower())

    def test_blocks_sql_drop_and_truncate(self):
        blocked_cmds = [
            "DROP TABLE users;",
            "drop table customers",
            "TRUNCATE TABLE logs;",
            "truncate metrics;"
        ]
        for cmd in blocked_cmds:
            allowed, _ = check_command(cmd)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked")

    def test_blocks_unrestricted_delete(self):
        blocked_cmds = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM orders;"
        ]
        for cmd in blocked_cmds:
            allowed, reason = check_command(cmd)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked")

    def test_allows_safe_operations(self):
        allowed_cmds = [
            "ls -la",
            "git status",
            "git push origin feat/awesome",
            "rm single_file.txt",
            "SELECT * FROM users WHERE active = 1;",
            "DELETE FROM users WHERE id = 42;",
            "npm test",
            "python3 -m unittest"
        ]
        for cmd in allowed_cmds:
            allowed, reason = check_command(cmd)
            self.assertTrue(allowed, f"Expected '{cmd}' to be allowed, but was blocked for: {reason}")

if __name__ == "__main__":
    unittest.main()
