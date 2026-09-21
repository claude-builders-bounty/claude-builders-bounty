#!/usr/bin/env python3
"""
Unit tests for Claude Code pre-tool-use hook: block-destructive-bash.
Validates pattern detection, logging, and Claude Code JSON stdin compatibility.
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# Add hook directory to path
HOOK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOK_DIR))

import block_destructive


class TestBlockDestructiveHook(unittest.TestCase):

    def test_rm_rf_blocked(self):
        dangerous = [
            "rm -rf /",
            "rm -rf ./build",
            "rm -fr /tmp/test",
            "rm -r -f node_modules",
            "rm -f -r logs",
            "rm --recursive --force /var/data",
            "sudo rm -rf /etc"
        ]
        for cmd in dangerous:
            is_safe, reason = block_destructive.check_command_safety(cmd)
            self.assertFalse(is_safe, f"Command '{cmd}' should have been blocked!")
            self.assertIn("Recursive file deletion", reason)

    def test_drop_table_blocked(self):
        dangerous = [
            "DROP TABLE users;",
            "drop table if exists orders",
            "DROP DATABASE production;",
            "DROP SCHEMA public CASCADE;",
            "psql -c 'DROP TABLE secrets;'",
        ]
        for cmd in dangerous:
            is_safe, reason = block_destructive.check_command_safety(cmd)
            self.assertFalse(is_safe, f"Command '{cmd}' should have been blocked!")
            self.assertIn("DROP", reason)

    def test_force_push_blocked(self):
        dangerous = [
            "git push origin main --force",
            "git push -f",
            "git push origin feature -f",
            "git push --force-with-lease origin main"
        ]
        for cmd in dangerous:
            is_safe, reason = block_destructive.check_command_safety(cmd)
            self.assertFalse(is_safe, f"Command '{cmd}' should have been blocked!")
            self.assertIn("Force-push", reason)

    def test_truncate_blocked(self):
        dangerous = [
            "TRUNCATE TABLE audit_log;",
            "truncate users;",
            "TRUNCATE `sessions`"
        ]
        for cmd in dangerous:
            is_safe, reason = block_destructive.check_command_safety(cmd)
            self.assertFalse(is_safe, f"Command '{cmd}' should have been blocked!")
            self.assertIn("TRUNCATE", reason)

    def test_unbounded_delete_blocked(self):
        dangerous = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM `orders`",
            "DELETE FROM customers /* no where */ ;"
        ]
        for cmd in dangerous:
            is_safe, reason = block_destructive.check_command_safety(cmd)
            self.assertFalse(is_safe, f"Command '{cmd}' should have been blocked!")
            self.assertIn("DELETE without a WHERE clause", reason)

    def test_safe_commands_allowed(self):
        safe = [
            "ls -la",
            "git status",
            "git push origin main",
            "git commit -m 'feat: add feature'",
            "rm test.txt",
            "rm -f single_file.log",
            "DELETE FROM users WHERE id = 42;",
            "delete from sessions where expired_at < now()",
            "python3 -m unittest discover",
            "npm test",
            "cargo build --release"
        ]
        for cmd in safe:
            is_safe, reason = block_destructive.check_command_safety(cmd)
            self.assertTrue(is_safe, f"Command '{cmd}' should be allowed! Blocked because: {reason}")
            self.assertIsNone(reason)

    def test_audit_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_log_dir = Path(tmpdir)
            block_destructive.LOG_DIR = test_log_dir
            block_destructive.LOG_FILE = test_log_dir / "blocked.log"

            cmd = "rm -rf /test_path"
            reason = "Recursive file deletion test"
            project = "/home/developer/app"

            block_destructive.log_blocked_attempt(cmd, reason, project)

            self.assertTrue(block_destructive.LOG_FILE.exists())
            content = block_destructive.LOG_FILE.read_text(encoding="utf-8")
            self.assertIn("BLOCKED: Recursive file deletion test", content)
            self.assertIn("Command: rm -rf /test_path", content)
            self.assertIn("Project: /home/developer/app", content)


if __name__ == "__main__":
    unittest.main()
