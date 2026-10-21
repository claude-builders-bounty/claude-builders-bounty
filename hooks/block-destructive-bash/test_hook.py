#!/usr/bin/env python3
"""
Unit Test Suite for Claude Code Pre-Tool-Use Destructive Command Blocker
Verifies all 5 blocked patterns, allowed safe commands, audit logging, and exit codes.
"""

import unittest
import os
import sys
import subprocess
import json
import tempfile
import shutil

HOOK_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "block_destructive_bash.py"))


class TestDestructiveCommandBlocker(unittest.TestCase):
    def setUp(self):
        # Set up a mock home directory to test isolated logging
        self.test_dir = tempfile.mkdtemp()
        self.mock_claude_dir = os.path.join(self.test_dir, ".claude", "hooks")
        os.makedirs(self.mock_claude_dir, exist_ok=True)
        self.mock_log = os.path.join(self.mock_claude_dir, "blocked.log")

        # Copy environment and redirect HOME / USERPROFILE
        self.env = os.environ.copy()
        self.env["HOME"] = self.test_dir
        self.env["USERPROFILE"] = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_hook_cli(self, command_str):
        """Runs the hook script with command string as CLI arguments."""
        result = subprocess.run(
            [sys.executable, HOOK_SCRIPT, command_str],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=self.env,
        )
        return result

    def run_hook_json_stdin(self, command_str, project_path="/workspace/test-project"):
        """Runs the hook script feeding Claude Code JSON to stdin."""
        payload = json.dumps({
            "tool": "Bash",
            "tool_input": {
                "command": command_str
            },
            "project_path": project_path
        })
        result = subprocess.run(
            [sys.executable, HOOK_SCRIPT],
            input=payload,
            capture_output=True,
            text=True,
            env=self.env,
        )
        return result

    # -------------------------------------------------------------
    # 1. Blocked Pattern: rm -rf
    # -------------------------------------------------------------
    def test_block_rm_rf(self):
        cases = [
            "rm -rf /",
            "rm -rf node_modules",
            "rm -fr dist/",
            "rm -r -f .git",
            "rm -f -r build",
            "rm -rfi /tmp/cache",
            "rm --recursive --force .cache",
            "sudo rm -rf /var/log",
            "cd /tmp && rm -rf test",
        ]
        for cmd in cases:
            res = self.run_hook_cli(cmd)
            self.assertEqual(res.returncode, 2, f"Expected blocked: {cmd}")
            self.assertIn("[BLOCKED]", res.stderr)
            self.assertIn("Recursive force removal", res.stderr)

    # -------------------------------------------------------------
    # 2. Blocked Pattern: DROP TABLE / DATABASE / SCHEMA
    # -------------------------------------------------------------
    def test_block_drop_table(self):
        cases = [
            "DROP TABLE users;",
            "drop table if exists customers",
            "sqlite3 dev.db 'DROP TABLE orders;'",
            "psql -c 'DROP DATABASE production'",
            "DROP SCHEMA analytics CASCADE;",
            "DROP VIEW active_users;",
        ]
        for cmd in cases:
            res = self.run_hook_cli(cmd)
            self.assertEqual(res.returncode, 2, f"Expected blocked: {cmd}")
            self.assertIn("Database drop statement", res.stderr)

    # -------------------------------------------------------------
    # 3. Blocked Pattern: git push --force / -f
    # -------------------------------------------------------------
    def test_block_git_push_force(self):
        cases = [
            "git push --force",
            "git push origin main --force",
            "git push -f",
            "git push origin master -f",
            "git push origin +main",
            "git push origin main --force-with-lease",
        ]
        for cmd in cases:
            res = self.run_hook_cli(cmd)
            self.assertEqual(res.returncode, 2, f"Expected blocked: {cmd}")
            self.assertIn("Force git push", res.stderr)

    # -------------------------------------------------------------
    # 4. Blocked Pattern: TRUNCATE [TABLE]
    # -------------------------------------------------------------
    def test_block_truncate(self):
        cases = [
            "TRUNCATE TABLE logs;",
            "truncate table user_sessions",
            "TRUNCATE audit_events",
            "sqlite3 data.db 'TRUNCATE TABLE metrics'",
        ]
        for cmd in cases:
            res = self.run_hook_cli(cmd)
            self.assertEqual(res.returncode, 2, f"Expected blocked: {cmd}")
            self.assertIn("Database truncation statement", res.stderr)

    # -------------------------------------------------------------
    # 5. Blocked Pattern: DELETE FROM without WHERE clause
    # -------------------------------------------------------------
    def test_block_blind_delete_from(self):
        cases = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM orders",
            "sqlite3 db.sqlite 'DELETE FROM logs;'",
        ]
        for cmd in cases:
            res = self.run_hook_cli(cmd)
            self.assertEqual(res.returncode, 2, f"Expected blocked: {cmd}")
            self.assertIn("Blind SQL deletion", res.stderr)

    # -------------------------------------------------------------
    # Allowed Commands: Safe operations MUST NOT be blocked (Exit 0)
    # -------------------------------------------------------------
    def test_allow_safe_commands(self):
        safe_cases = [
            "rm file.txt",
            "rm -r single_dir",  # rm without -f
            "git push origin feature-branch",
            "git push",
            "SELECT * FROM users WHERE active = 1;",
            "DELETE FROM users WHERE id = 42;",
            "delete from accounts where balance = 0;",
            "npm run test",
            "cargo build --release",
            "python -m unittest",
            "ls -la",
            "cat README.md",
            "git status",
        ]
        for cmd in safe_cases:
            res = self.run_hook_cli(cmd)
            self.assertEqual(res.returncode, 0, f"Expected allowed (exit 0): {cmd}")
            self.assertEqual(res.stderr.strip(), "")

    # -------------------------------------------------------------
    # Stdin JSON Payload parsing (Claude Code hook protocol)
    # -------------------------------------------------------------
    def test_json_stdin_blocking_and_logging(self):
        test_cmd = "rm -rf /critical/data"
        test_project = "/Users/dev/cool-saas"

        res = self.run_hook_json_stdin(test_cmd, test_project)
        self.assertEqual(res.returncode, 2)
        self.assertIn("[BLOCKED]", res.stderr)
        self.assertIn(test_project, res.stderr)

        # Verify log file exists in mock directory and contains proper records
        self.assertTrue(os.path.exists(self.mock_log), "blocked.log should be created")
        with open(self.mock_log, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(test_cmd, content)
            self.assertIn(test_project, content)
            self.assertIn("Recursive force removal", content)


if __name__ == "__main__":
    unittest.main()
