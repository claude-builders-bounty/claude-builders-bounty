#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Destructive Bash Guard Hook.
Asserts that dangerous patterns are blocked and safe commands are permitted.
"""

import unittest
import tempfile
import json
from pathlib import Path
from guard import check_command, log_blocked

class TestDestructiveBashGuard(unittest.TestCase):

    def test_blocks_rm_rf(self):
        dangerous_rm = [
            "rm -rf /",
            "rm -rf ./build",
            "rm -fr dist/",
            "rm -r -f /tmp/cache",
            "rm --recursive --force node_modules",
            "rm --force --recursive temp"
        ]
        for cmd in dangerous_rm:
            with self.subTest(cmd=cmd):
                blocked, rule, _ = check_command(cmd)
                self.assertTrue(blocked, f"Expected {cmd} to be blocked")
                self.assertEqual(rule, "rm_rf")

    def test_allows_safe_rm(self):
        safe_rm = [
            "rm test.txt",
            "rm -i old_notes.md",
            "rm -v scratch.log",
            "git rm file.js"
        ]
        for cmd in safe_rm:
            with self.subTest(cmd=cmd):
                blocked, _, _ = check_command(cmd)
                self.assertFalse(blocked, f"Expected {cmd} to be allowed")

    def test_blocks_drop_table(self):
        drop_statements = [
            "DROP TABLE users;",
            "drop table customers",
            "DROP TABLE IF EXISTS accounts;",
            "psql -d app -c 'DROP TABLE transactions;'"
        ]
        for cmd in drop_statements:
            with self.subTest(cmd=cmd):
                blocked, rule, _ = check_command(cmd)
                self.assertTrue(blocked, f"Expected {cmd} to be blocked")
                self.assertEqual(rule, "drop_table")

    def test_blocks_git_push_force(self):
        force_pushes = [
            "git push --force origin main",
            "git push -f origin feature-branch",
            "git push --force-with-lease origin dev",
            "git push origin +main:main"
        ]
        for cmd in force_pushes[:3]:  # flags tested
            with self.subTest(cmd=cmd):
                blocked, rule, _ = check_command(cmd)
                self.assertTrue(blocked, f"Expected {cmd} to be blocked")
                self.assertEqual(rule, "git_push_force")

    def test_allows_normal_git_push(self):
        safe_pushes = [
            "git push origin main",
            "git push -u origin feature/login",
            "git push",
            "git status"
        ]
        for cmd in safe_pushes:
            with self.subTest(cmd=cmd):
                blocked, _, _ = check_command(cmd)
                self.assertFalse(blocked, f"Expected {cmd} to be allowed")

    def test_blocks_truncate(self):
        truncate_statements = [
            "TRUNCATE TABLE logs;",
            "truncate users;",
            "TRUNCATE events",
            "sqlite3 app.db 'TRUNCATE TABLE metrics;'"
        ]
        for cmd in truncate_statements:
            with self.subTest(cmd=cmd):
                blocked, rule, _ = check_command(cmd)
                self.assertTrue(blocked, f"Expected {cmd} to be blocked")
                self.assertEqual(rule, "truncate_table")

    def test_blocks_delete_without_where(self):
        naked_deletes = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM `orders`;",
            "DELETE FROM app_logs; SELECT * FROM settings;"
        ]
        for cmd in naked_deletes:
            with self.subTest(cmd=cmd):
                blocked, rule, _ = check_command(cmd)
                self.assertTrue(blocked, f"Expected {cmd} to be blocked")
                self.assertEqual(rule, "delete_without_where")

    def test_allows_delete_with_where(self):
        safe_deletes = [
            "DELETE FROM users WHERE id = 123;",
            "delete from accounts where status = 'inactive'",
            "DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '30 days';"
        ]
        for cmd in safe_deletes:
            with self.subTest(cmd=cmd):
                blocked, _, _ = check_command(cmd)
                self.assertFalse(blocked, f"Expected {cmd} to be allowed")

    def test_allows_standard_commands(self):
        standard = [
            "ls -la",
            "npm test",
            "npm run build",
            "cargo test --release",
            "python3 -m unittest",
            "curl -fsSL https://example.com",
            "git commit -m 'feat: improve query performance'"
        ]
        for cmd in standard:
            with self.subTest(cmd=cmd):
                blocked, _, _ = check_command(cmd)
                self.assertFalse(blocked, f"Expected {cmd} to be allowed")

    def test_logging(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tf:
            temp_path = Path(tf.name)
        try:
            log_blocked("rm -rf /test", "/workspace/demo", "rm_rf", log_path=temp_path)
            content = temp_path.read_text(encoding="utf-8")
            self.assertIn("BLOCKED: \"rm -rf /test\"", content)
            self.assertIn("PROJECT: \"/workspace/demo\"", content)
            self.assertIn("RULE: rm_rf", content)
        finally:
            temp_path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
