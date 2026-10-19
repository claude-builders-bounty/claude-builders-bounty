#!/usr/bin/env python3
"""
Comprehensive test suite for Claude Code Destructive Bash Command Interceptor Hook.
Tests all acceptance criteria patterns, benign command non-interference, and logging.
"""
import unittest
import subprocess
import os
import sys
import json
import tempfile
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "block_destructive_bash.py"

class TestDestructiveBashHook(unittest.TestCase):
    def run_hook(self, command: str, as_json: bool = False) -> subprocess.CompletedProcess:
        if as_json:
            payload = json.dumps({
                "tool_name": "bash",
                "tool_input": {"command": command}
            })
            return subprocess.run(
                [sys.executable, str(HOOK_SCRIPT)],
                input=payload,
                capture_output=True,
                text=True
            )
        else:
            return subprocess.run(
                [sys.executable, str(HOOK_SCRIPT), command],
                capture_output=True,
                text=True
            )

    # 1. rm -rf variations
    def test_blocks_rm_rf(self):
        dangerous_commands = [
            "rm -rf /",
            "rm -fr /var/log",
            "rm -r -f build/",
            "rm --recursive --force dist/",
            "rm -rf ./node_modules && npm i"
        ]
        for cmd in dangerous_commands:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 1, f"Failed to block: {cmd}")
            self.assertIn("Command Blocked", res.stderr)
            self.assertIn("Recursive force removal", res.stderr)

    # 2. DROP TABLE / DATABASE / SCHEMA
    def test_blocks_drop_table(self):
        dangerous_commands = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            "psql -c 'DROP DATABASE production'",
            "DROP SCHEMA public CASCADE"
        ]
        for cmd in dangerous_commands:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 1, f"Failed to block: {cmd}")
            self.assertIn("Database Drop Operation", res.stderr)

    # 3. git push --force / -f
    def test_blocks_git_push_force(self):
        dangerous_commands = [
            "git push --force origin main",
            "git push -f",
            "git push origin +main",
            "git push --force"
        ]
        for cmd in dangerous_commands:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 1, f"Failed to block: {cmd}")
            self.assertIn("Force git push", res.stderr)

    # 4. TRUNCATE TABLE
    def test_blocks_truncate(self):
        dangerous_commands = [
            "TRUNCATE TABLE sessions;",
            "truncate table logs",
            "sqlite3 app.db 'TRUNCATE events;'"
        ]
        for cmd in dangerous_commands:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 1, f"Failed to block: {cmd}")
            self.assertIn("Table Truncation", res.stderr)

    # 5. DELETE FROM without WHERE
    def test_blocks_unconstrained_delete(self):
        dangerous_commands = [
            "DELETE FROM users;",
            "delete from accounts",
            "sqlite3 db.sqlite 'DELETE FROM orders;'"
        ]
        for cmd in dangerous_commands:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 1, f"Failed to block: {cmd}")
            self.assertIn("Unconstrained SQL Delete", res.stderr)

    # 6. Benign commands MUST NOT be blocked
    def test_allows_benign_commands(self):
        safe_commands = [
            "rm file.txt",
            "rm -r temp_dir",  # without -f
            "git push origin feat/new-ui",
            "git status",
            "DELETE FROM users WHERE id = 42;",
            "delete from sessions where expired_at < now();",
            "SELECT * FROM users;",
            "npm test",
            "pytest tests/ -v",
            "cargo build --release"
        ]
        for cmd in safe_commands:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 0, f"Incorrectly blocked safe command: {cmd}")
            self.assertEqual(res.stderr, "")

    # 7. Claude Code JSON payload via stdin
    def test_json_payload_interception(self):
        res = self.run_hook("rm -rf /tmp/test", as_json=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Command Blocked", res.stderr)

        res_safe = self.run_hook("echo 'hello'", as_json=True)
        self.assertEqual(res_safe.returncode, 0)

if __name__ == "__main__":
    unittest.main()
