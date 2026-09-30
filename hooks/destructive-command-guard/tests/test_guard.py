#!/usr/bin/env python3
"""
Test suite for Claude Code Destructive Command Guard
Verifies all acceptance criteria for Bounty #3.
"""

import os
import sys
import json
import tempfile
import unittest
import importlib.util
from pathlib import Path

# Load hook dynamically
from importlib.machinery import SourceFileLoader
HOOK_PATH = Path(__file__).parent.parent / "pre-tool-use"
guard = SourceFileLoader("guard", str(HOOK_PATH)).load_module()

class TestDestructiveCommandGuard(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked_commands = [
            "rm -rf /tmp/data",
            "rm -fr ./dist",
            "rm -r -f node_modules",
            "rm -f -r .cache",
            "rm --recursive --force /var/log",
            "sudo rm -rf /var/run",
            "bash -c 'rm -rf /data'"
        ]
        for cmd in blocked_commands:
            blocked, reason = guard.check_destructive(cmd)
            self.assertTrue(blocked, f"Should block: {cmd}")
            self.assertIn("rm -rf", reason)

    def test_blocks_drop_table(self):
        blocked_commands = [
            "DROP TABLE users;",
            "drop table if exists orders",
            "psql -d app -c 'DROP TABLE accounts;'",
            "sqlite3 app.db 'DROP TABLE sessions;'"
        ]
        for cmd in blocked_commands:
            blocked, reason = guard.check_destructive(cmd)
            self.assertTrue(blocked, f"Should block: {cmd}")
            self.assertIn("DROP TABLE", reason)

    def test_blocks_git_force_push(self):
        blocked_commands = [
            "git push origin main --force",
            "git push origin feat/test -f",
            "git push -f",
            "git push origin HEAD:main --force-with-lease"
        ]
        for cmd in blocked_commands:
            blocked, reason = guard.check_destructive(cmd)
            self.assertTrue(blocked, f"Should block: {cmd}")
            self.assertIn("git push", reason)

    def test_blocks_truncate(self):
        blocked_commands = [
            "TRUNCATE TABLE logs",
            "TRUNCATE users;",
            "truncate `orders`"
        ]
        for cmd in blocked_commands:
            blocked, reason = guard.check_destructive(cmd)
            self.assertTrue(blocked, f"Should block: {cmd}")
            self.assertIn("TRUNCATE", reason)

    def test_blocks_unbounded_delete_from(self):
        blocked_commands = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM logs WHERE 1=1; DELETE FROM users;"
        ]
        for cmd in blocked_commands:
            blocked, reason = guard.check_destructive(cmd)
            self.assertTrue(blocked, f"Should block: {cmd}")
            self.assertIn("DELETE FROM", reason)

    def test_allows_safe_commands(self):
        safe_commands = [
            "ls -la",
            "cat package.json",
            "rm single_file.txt",
            "git status",
            "git push origin main",
            "git commit -m 'feat: add delete feature'",
            "DELETE FROM users WHERE id = 42;",
            "DELETE FROM orders WHERE status = 'expired' AND created_at < NOW();",
            "npm run test",
            "cargo build --release",
            "python3 -m unittest discover",
            "echo 'rm -rf is dangerous'"
        ]
        for cmd in safe_commands:
            blocked, reason = guard.check_destructive(cmd)
            self.assertFalse(blocked, f"Should allow safe command: {cmd} (blocked reason: {reason})")

    def test_json_stdin_parsing(self):
        json_payload = json.dumps({
            "tool": "Bash",
            "tool_input": {"command": "rm -rf /tmp/target"},
            "cwd": "/workspace/my-project"
        })
        cmd, cwd = guard.parse_input(json_payload)
        self.assertEqual(cmd, "rm -rf /tmp/target")
        self.assertEqual(cwd, "/workspace/my-project")

    def test_audit_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_log = os.path.join(tmpdir, "test_blocked.log")
            guard.BLOCKED_LOG_PATH = test_log
            
            cmd = "DROP TABLE test_users;"
            cwd = "/test/project"
            reason = "Destructive SQL operation (DROP TABLE)"
            
            guard.log_blocked_attempt(cmd, cwd, reason)
            
            self.assertTrue(os.path.exists(test_log))
            with open(test_log, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("[BLOCKED]", content)
            self.assertIn("DROP TABLE test_users;", content)
            self.assertIn("/test/project", content)

if __name__ == "__main__":
    unittest.main()
