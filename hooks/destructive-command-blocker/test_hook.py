#!/usr/bin/env python3
"""
Unit tests for Claude Code Pre-Tool-Use Security Hook
Tests destructive pattern detection, log file generation, and non-destructive command pass-through.
"""

import unittest
import subprocess
import os
import json
import tempfile
from pathlib import Path
import shutil

HOOK_SCRIPT = Path(__file__).parent / "pre_tool_use.py"

class TestDestructiveCommandBlocker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_log_file = Path(self.temp_dir) / "blocked.log"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_hook(self, command_or_payload, is_json=False):
        """Runs the hook with CLI argument or JSON stdin."""
        env = os.environ.copy()
        if is_json:
            proc = subprocess.run(
                ["python3", str(HOOK_SCRIPT)],
                input=json.dumps(command_or_payload),
                text=True,
                capture_output=True,
                env=env
            )
        else:
            proc = subprocess.run(
                ["python3", str(HOOK_SCRIPT), command_or_payload],
                text=True,
                capture_output=True,
                env=env
            )
        return proc

    # 1. Test rm -rf variations
    def test_blocks_rm_rf_variants(self):
        commands = [
            "rm -rf /var/data",
            "rm -fr /tmp/build",
            "rm -r -f node_modules",
            "rm -f -r cache",
            "rm --recursive --force ./dist",
            "rm --force --recursive temp_dir",
            "rm -rf ./*"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 2, f"Expected {cmd} to be blocked")
                self.assertIn("Recursive Force Delete", proc.stderr)

    # 2. Test DROP TABLE variations
    def test_blocks_drop_table(self):
        commands = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            'DROP TABLE "audit_logs"',
            "DROP TABLE `sessions`"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 2, f"Expected {cmd} to be blocked")
                self.assertIn("Drop Database Table", proc.stderr)

    # 3. Test git push --force variations
    def test_blocks_git_push_force(self):
        commands = [
            "git push --force",
            "git push origin main --force",
            "git push -f origin main",
            "git push origin +main:main"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 2, f"Expected {cmd} to be blocked")
                self.assertIn("Force Push Git Branch", proc.stderr)

    # 4. Test TRUNCATE variations
    def test_blocks_truncate(self):
        commands = [
            "TRUNCATE TABLE transactions;",
            "truncate table events",
            "TRUNCATE audit_log",
            "truncate `users`"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 2, f"Expected {cmd} to be blocked")
                self.assertIn("Truncate Database Table", proc.stderr)

    # 5. Test DELETE FROM without WHERE
    def test_blocks_delete_without_where(self):
        commands = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM `orders`",
            "DELETE FROM customers;"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 2, f"Expected {cmd} to be blocked")
                self.assertIn("Unconstrained Delete", proc.stderr)

    # 6. Test safe DELETE with WHERE clause allowed
    def test_allows_safe_delete_with_where(self):
        commands = [
            "DELETE FROM users WHERE id = 123;",
            "delete from sessions where expires_at < NOW()",
            "DELETE FROM items WHERE status = 'archived'"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 0, f"Expected {cmd} to be allowed")

    # 7. Test benign commands are not interfered with
    def test_allows_normal_commands(self):
        commands = [
            "ls -la",
            "git status",
            "git push origin main",
            "git checkout -b feature/auth",
            "npm test",
            "pytest tests/",
            "cat README.md",
            "rm test.txt",
            "mkdir -p src/components",
            "python3 main.py"
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                proc = self.run_hook(cmd)
                self.assertEqual(proc.returncode, 0, f"Expected {cmd} to be allowed")

    # 8. Test Claude Code Hook JSON payload via stdin
    def test_claude_code_json_stdin_blocked(self):
        payload = {
            "tool": "bash",
            "tool_input": {
                "command": "rm -rf /workspace/project"
            },
            "cwd": "/workspace/project"
        }
        proc = self.run_hook(payload, is_json=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Recursive Force Delete", proc.stderr)

    def test_claude_code_json_stdin_allowed(self):
        payload = {
            "tool": "bash",
            "tool_input": {
                "command": "git commit -m 'feat: add security hook'"
            },
            "cwd": "/workspace/project"
        }
        proc = self.run_hook(payload, is_json=True)
        self.assertEqual(proc.returncode, 0)

if __name__ == "__main__":
    unittest.main()
