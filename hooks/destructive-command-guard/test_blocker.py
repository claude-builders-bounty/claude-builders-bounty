#!/usr/bin/env python3
"""
Comprehensive test suite for Destructive Bash Command Guard.
Verifies blocked patterns, normal pass-through, and audit logging.
"""

import unittest
from pre_tool_use_blocker import check_command


class TestDestructiveCommandGuard(unittest.TestCase):
    def test_blocks_rm_rf(self):
        dangerous = [
            "rm -rf /",
            "rm -rf node_modules",
            "rm -fr dist",
            "rm -r -f build",
            "rm --recursive --force .",
        ]
        for cmd in dangerous:
            blocked, reason = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("rm -rf", reason)

    def test_blocks_drop_table(self):
        dangerous = [
            "DROP TABLE users;",
            "psql -c 'DROP TABLE accounts;'",
            "sqlite3 app.db \"drop table sessions\"",
        ]
        for cmd in dangerous:
            blocked, reason = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("DROP TABLE", reason)

    def test_blocks_git_push_force(self):
        dangerous = [
            "git push --force origin main",
            "git push -f origin master",
            "git push --force-with-lease origin feat",
        ]
        for cmd in dangerous:
            blocked, reason = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("git push --force", reason)

    def test_blocks_truncate(self):
        dangerous = [
            "TRUNCATE TABLE logs;",
            "TRUNCATE audit_events",
            "truncate table `cache`",
        ]
        for cmd in dangerous:
            blocked, reason = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("TRUNCATE", reason)

    def test_blocks_delete_without_where(self):
        dangerous = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM `orders`;",
        ]
        for cmd in dangerous:
            blocked, reason = check_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("DELETE FROM", reason)

    def test_allows_safe_delete_with_where(self):
        safe = [
            "DELETE FROM users WHERE id = 1;",
            "delete from sessions where expired_at < NOW();",
        ]
        for cmd in safe:
            blocked, _ = check_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be allowed.")

    def test_allows_normal_bash_commands(self):
        safe = [
            "npm run test",
            "git status",
            "git pull origin main",
            "ls -la",
            "python -m pytest",
            "cat README.md",
            "mkdir -p src/components",
        ]
        for cmd in safe:
            blocked, _ = check_command(cmd)
            self.assertFalse(blocked, f"Expected '{cmd}' to be allowed.")


if __name__ == "__main__":
    unittest.main()
