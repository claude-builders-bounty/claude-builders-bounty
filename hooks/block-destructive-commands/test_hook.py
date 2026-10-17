#!/usr/bin/env python3
"""
Unit and integration tests for block_destructive_commands hook.
Verifies all acceptance criteria from Bounty #3.
"""

import unittest
import os
import tempfile
import json
import subprocess
from block_destructive_commands import check_command

class TestDestructiveCommandBlocker(unittest.TestCase):

    def test_blocks_rm_rf(self):
        blocked_commands = [
            "rm -rf /",
            "rm -rf ./node_modules",
            "rm -fr tmp/",
            "rm -r -f build/",
            "rm --recursive --force dist/"
        ]
        for cmd in blocked_commands:
            is_blocked, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")

    def test_blocks_drop_table(self):
        blocked_commands = [
            "DROP TABLE users;",
            "psql -c 'drop table orders'",
            "DROP DATABASE production;",
            "DROP SCHEMA public CASCADE;"
        ]
        for cmd in blocked_commands:
            is_blocked, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")

    def test_blocks_git_push_force(self):
        blocked_commands = [
            "git push origin main --force",
            "git push -f",
            "git push origin +main",
            "git push origin master -f"
        ]
        for cmd in blocked_commands:
            is_blocked, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")

    def test_blocks_truncate(self):
        blocked_commands = [
            "TRUNCATE users;",
            "TRUNCATE TABLE transactions;",
            "sqlite3 app.db 'truncate accounts'"
        ]
        for cmd in blocked_commands:
            is_blocked, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")

    def test_blocks_delete_without_where(self):
        blocked_commands = [
            "DELETE FROM users;",
            "DELETE FROM `customers`",
            "DELETE FROM orders"
        ]
        for cmd in blocked_commands:
            is_blocked, _ = check_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")

    def test_allows_safe_delete_with_where(self):
        safe_commands = [
            "DELETE FROM users WHERE id = 5;",
            "DELETE FROM sessions WHERE expires_at < NOW();"
        ]
        for cmd in safe_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Should have allowed: {cmd}")

    def test_allows_normal_commands(self):
        safe_commands = [
            "git status",
            "git commit -m 'feat: update code'",
            "npm test",
            "rm file.txt",
            "ls -la",
            "python3 app.py",
            "SELECT * FROM users;"
        ]
        for cmd in safe_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Should have allowed: {cmd}")

if __name__ == "__main__":
    unittest.main()
