#!/usr/bin/env python3
"""
Unit tests for Claude Code pre-tool-use security hook (block_destructive.py).
Verifies all acceptance criteria for issue #3.
"""

import unittest
import os
import tempfile
import json
import subprocess
import sys

# Import functions from hooks.block_destructive
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hooks.block_destructive import check_command, log_blocked_attempt, is_delete_from_without_where


class TestBlockDestructiveHook(unittest.TestCase):

    def test_rm_rf_patterns(self):
        blocked_commands = [
            "rm -rf /tmp/foo",
            "rm -fr .",
            "rm -r -f build/",
            "rm --recursive --force node_modules",
            "sudo rm -rf /var/log/*"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertIn("Recursive force removal", reason)

    def test_drop_table_patterns(self):
        blocked_commands = [
            "DROP TABLE users;",
            "drop table audit_logs",
            "psql -c 'DROP TABLE accounts;'"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertIn("DROP TABLE", reason)

    def test_git_push_force_patterns(self):
        blocked_commands = [
            "git push origin main --force",
            "git push -f",
            "git push --force-with-lease origin feature"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertIn("git push", reason)

    def test_truncate_patterns(self):
        blocked_commands = [
            "TRUNCATE TABLE sessions;",
            "truncate logs",
            "mysql -e 'TRUNCATE TABLE cache'"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertIn("TRUNCATE", reason)

    def test_delete_from_without_where(self):
        blocked_commands = [
            "DELETE FROM users;",
            "delete from sessions",
            "sqlite3 app.db 'DELETE FROM logs'"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Should block: {cmd}")
            self.assertIn("missing a WHERE clause", reason)

    def test_delete_from_with_where_allowed(self):
        allowed_commands = [
            "DELETE FROM users WHERE id = 42;",
            "delete from sessions where expired = 1",
            "DELETE FROM logs WHERE created_at < '2026-01-01'"
        ]
        for cmd in allowed_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Should allow: {cmd}")

    def test_safe_commands_allowed(self):
        safe_commands = [
            "git status",
            "ls -la",
            "npm test",
            "python3 -m unittest discover",
            "pytest tests/",
            "git log -n 5",
            "echo 'hello world'",
            "rm clean_file.txt"
        ]
        for cmd in safe_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Should allow safe command: {cmd}")

    def test_logging_functionality(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_log:
            log_path = tmp_log.name

        try:
            log_blocked_attempt("rm -rf /test", "/home/user/project", "Recursive force removal", log_path=log_path)

            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("BLOCKED", content)
            self.assertIn("/home/user/project", content)
            self.assertIn("rm -rf /test", content)
            self.assertIn("Recursive force removal", content)
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_cli_execution_blocked(self):
        hook_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hooks", "block_destructive.py"))
        proc = subprocess.run([sys.executable, hook_script, "rm -rf /"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("SECURITY HOOK BLOCKED COMMAND", proc.stderr)

    def test_cli_execution_allowed(self):
        hook_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hooks", "block_destructive.py"))
        proc = subprocess.run([sys.executable, hook_script, "git status"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_json_stdin_input(self):
        hook_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hooks", "block_destructive.py"))
        input_data = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "DROP TABLE users;"},
            "cwd": "/home/user/app"
        })
        proc = subprocess.run([sys.executable, hook_script], input=input_data, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DROP TABLE", proc.stderr)


if __name__ == "__main__":
    unittest.main()
