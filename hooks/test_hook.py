#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Pre-Tool-Use Destructive Command Hook.
Validates all acceptance criteria required by Bounty #3.
"""

import unittest
import os
import tempfile
import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "pre-tool-use.py"

class TestDestructiveCommandHook(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "blocked.log")
        os.environ["HOME"] = self.test_dir
        os.environ["USERPROFILE"] = self.test_dir

    def run_hook(self, command_str):
        payload = json.dumps({"command": command_str, "project_path": "/workspace/project"})
        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=payload,
            text=True,
            capture_output=True
        )
        return proc.returncode, proc.stderr, proc.stdout

    def test_blocks_rm_rf(self):
        cases = [
            "rm -rf /",
            "rm -rf ./build",
            "rm -fr dist",
            "sudo rm -r -f /var/log"
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 1, f"Expected {cmd} to be blocked")
                self.assertIn("Recursive Force Removal", stderr)

    def test_blocks_drop_table(self):
        cases = [
            "psql -c 'DROP TABLE users;'",
            "sqlite3 dev.db 'drop table accounts'",
            "DROP TABLE IF EXISTS orders;"
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 1, f"Expected {cmd} to be blocked")
                self.assertIn("SQL Drop Table", stderr)

    def test_blocks_truncate(self):
        cases = [
            "mysql -e 'TRUNCATE TABLE logs;'",
            "TRUNCATE users;"
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 1, f"Expected {cmd} to be blocked")
                self.assertIn("SQL Truncate Table", stderr)

    def test_blocks_unbounded_delete(self):
        bad_cases = [
            "DELETE FROM users;",
            "sqlite3 db.sqlite 'DELETE FROM sessions'"
        ]
        for cmd in bad_cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 1, f"Expected {cmd} to be blocked")
                self.assertIn("Unbounded SQL Delete", stderr)

    def test_allows_bounded_delete(self):
        safe_cases = [
            "DELETE FROM users WHERE id = 12;",
            "DELETE FROM sessions WHERE expired_at < NOW();"
        ]
        for cmd in safe_cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 0, f"Expected safe delete to pass: {cmd}")

    def test_blocks_git_force_push(self):
        cases = [
            "git push origin main --force",
            "git push -f origin master",
            "git push origin head --force-with-lease"
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 1, f"Expected {cmd} to be blocked")
                self.assertIn("Git Force Push", stderr)

    def test_allows_normal_commands(self):
        normal_cases = [
            "ls -la",
            "npm install",
            "pytest tests/",
            "git status",
            "git push origin feature/safe-branch",
            "rm test.txt",
            "cat README.md"
        ]
        for cmd in normal_cases:
            with self.subTest(cmd=cmd):
                code, stderr, _ = self.run_hook(cmd)
                self.assertEqual(code, 0, f"Expected {cmd} to be allowed")

if __name__ == "__main__":
    unittest.main()
