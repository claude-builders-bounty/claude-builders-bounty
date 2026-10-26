#!/usr/bin/env python3
"""
Unit Test Suite for Claude Code PreToolUse Safety Interceptor
Validates acceptance criteria for Bounty #3 ($100).
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

HOOK_SCRIPT = Path(__file__).parent.parent / "hooks" / "pre_tool_use_safety.py"


class TestClaudeSafetyHook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert HOOK_SCRIPT.exists(), f"Hook script not found at {HOOK_SCRIPT}"

    def run_hook(self, command: str) -> subprocess.CompletedProcess:
        """Executes hook with direct command."""
        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT), "--command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_blocks_recursive_rm_rf(self):
        blocked_cases = [
            "rm -rf /tmp/cache",
            "rm -fr build/",
            "rm -r -f node_modules",
            "rm -f -r .dist",
            "rm --recursive --force /var/data",
        ]
        for cmd in blocked_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 2, f"Expected {cmd} to be blocked (exit code 2)")
            self.assertIn("Recursive Force Removal", res.stderr)

    def test_blocks_git_force_push(self):
        blocked_cases = [
            "git push origin main --force",
            "git push -f",
            "git push origin feat/test --force-with-lease",
            "git push origin +main",
        ]
        for cmd in blocked_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 2, f"Expected {cmd} to be blocked")
            self.assertIn("Git Force Push", res.stderr)

    def test_blocks_drop_table(self):
        blocked_cases = [
            "DROP TABLE users;",
            "drop table `accounts`",
            "psql -c 'DROP TABLE customers;'",
        ]
        for cmd in blocked_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 2, f"Expected {cmd} to be blocked")
            self.assertIn("SQL Drop Table", res.stderr)

    def test_blocks_truncate(self):
        blocked_cases = [
            "TRUNCATE TABLE logs;",
            "truncate sessions",
        ]
        for cmd in blocked_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 2, f"Expected {cmd} to be blocked")
            self.assertIn("SQL Truncate Table", res.stderr)

    def test_blocks_unbounded_delete_from(self):
        blocked_cases = [
            "DELETE FROM users;",
            "delete from sessions",
        ]
        for cmd in blocked_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 2, f"Expected {cmd} to be blocked")
            self.assertIn("SQL Delete Without Where", res.stderr)

    def test_allows_safe_delete_with_where(self):
        allowed_cases = [
            "DELETE FROM users WHERE id = 12;",
            "delete from sessions where expires_at < NOW();",
        ]
        for cmd in allowed_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 0, f"Expected safe delete to pass: {cmd}")

    def test_allows_normal_bash_commands(self):
        allowed_cases = [
            "rm file.txt",
            "git push origin feature/new-page",
            "git status",
            "npm run build",
            "pnpm test",
            "SELECT * FROM users;",
            "echo 'rm -rf /' > script.sh",
        ]
        for cmd in allowed_cases:
            res = self.run_hook(cmd)
            self.assertEqual(res.returncode, 0, f"Expected normal command to pass: {cmd}")

    def test_audit_log_written_on_block(self):
        res = self.run_hook("rm -rf /test/audit_verification")
        self.assertEqual(res.returncode, 2)
        log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_file.exists(), "Expected blocked.log to exist")
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Recursive Force Removal", content)
        self.assertIn("/test/audit_verification", content)


if __name__ == "__main__":
    unittest.main()
