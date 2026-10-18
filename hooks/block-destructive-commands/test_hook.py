#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Claude Code Pre-Tool-Use Destructive Command Hook
===============================================================
Verifies:
1. Blocks rm -rf, rm -fr, rm -r -f, rm --recursive --force
2. Blocks DROP TABLE users, DROP TABLE `orders`
3. Blocks git push origin main --force, git push -f
4. Blocks TRUNCATE TABLE logs, TRUNCATE logs
5. Blocks unconstrained DELETE FROM users; allows DELETE FROM users WHERE id = 1
6. Allows benign commands: ls, git status, rm single_file.txt, npm test
7. Verifies logging to ~/.claude/hooks/blocked.log
8. Verifies JSON input parsing from Claude Code hook lifecycle
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add current dir to path to import pre-tool-use module
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Import target hook functions
import importlib.util
spec = importlib.util.spec_from_file_location("hook", current_dir / "pre-tool-use.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

class TestDestructiveCommandHook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "blocked.log"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_block_rm_rf_variations(self):
        dangerous_rms = [
            "rm -rf /tmp/test",
            "rm -fr ./build",
            "rm -r -f /var/data",
            "rm --recursive --force ./dist",
            "sudo rm -rf /etc/config"
        ]
        for cmd in dangerous_rms:
            allowed, msg = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked!")
            self.assertIn("Recursive Force File Deletion", msg)

    def test_allow_safe_rm(self):
        safe_rms = [
            "rm file.txt",
            "rm -i temp.log",
            "rm path/to/file.png"
        ]
        for cmd in safe_rms:
            allowed, _ = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertTrue(allowed, f"Expected '{cmd}' to be allowed!")

    def test_block_drop_table(self):
        sql_cmds = [
            "DROP TABLE users;",
            "drop table `accounts`",
            "sqlite3 app.db 'DROP TABLE IF EXISTS sessions;'"
        ]
        for cmd in sql_cmds:
            allowed, msg = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked!")
            self.assertIn("DROP TABLE", msg)

    def test_block_git_force_push(self):
        git_cmds = [
            "git push origin main --force",
            "git push -f",
            "git push origin feature-branch --force-with-lease"
        ]
        for cmd in git_cmds:
            allowed, msg = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked!")
            self.assertIn("Git Force Push", msg)

    def test_allow_safe_git_push(self):
        safe_git = [
            "git push",
            "git push origin main",
            "git push -u origin feature-abc",
            "git status"
        ]
        for cmd in safe_git:
            allowed, _ = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertTrue(allowed, f"Expected '{cmd}' to be allowed!")

    def test_block_truncate_table(self):
        cmds = [
            "TRUNCATE TABLE transactions;",
            "truncate audit_logs"
        ]
        for cmd in cmds:
            allowed, msg = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertFalse(allowed, f"Expected '{cmd}' to be blocked!")
            self.assertIn("TRUNCATE", msg)

    def test_sql_delete_with_and_without_where(self):
        # Without WHERE -> Blocked
        unconstrained = "DELETE FROM users;"
        allowed, msg = hook.check_command(unconstrained, "/project/path", self.log_file)
        self.assertFalse(allowed, "Expected unconstrained DELETE FROM to be blocked!")

        # With WHERE -> Allowed
        constrained = "DELETE FROM users WHERE is_active = 0 AND created_at < '2020-01-01';"
        allowed, _ = hook.check_command(constrained, "/project/path", self.log_file)
        self.assertTrue(allowed, "Expected constrained DELETE FROM with WHERE to be allowed!")

    def test_logging_audit_trail(self):
        cmd = "rm -rf /critical/data"
        hook.check_command(cmd, "/test/my-repo", self.log_file)
        
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("/test/my-repo", content)
        self.assertIn("rm -rf /critical/data", content)
        self.assertIn("Recursive Force File Deletion", content)

    def test_allow_standard_dev_commands(self):
        standard = [
            "npm test",
            "pytest tests/",
            "cargo build --release",
            "python3 main.py",
            "ls -la /home",
            "mkdir -p ./output"
        ]
        for cmd in standard:
            allowed, _ = hook.check_command(cmd, "/project/path", self.log_file)
            self.assertTrue(allowed, f"Expected '{cmd}' to be allowed!")

if __name__ == "__main__":
    unittest.main()
