#!/usr/bin/env python3
"""
Test suite for pre_tool_use.py Claude Code hook.
"""

import sys
import os
import json
import unittest
import tempfile
import subprocess

# Add repo root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hooks.pre_tool_use import (
    check_command,
    check_rm_rf,
    check_drop_table,
    check_git_force_push,
    check_truncate,
    check_delete_without_where,
    log_blocked_attempt,
)


class TestPreToolUseUnit(unittest.TestCase):

    # 1. rm -rf
    def test_rm_rf_blocked(self):
        blocked_cmds = [
            "rm -rf /",
            "rm -fr /tmp/dir",
            "rm -r -f /var/log",
            "rm --recursive --force /node_modules",
            "rm -rfv build/",
            "rm -vfr build/",
        ]
        for cmd in blocked_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, reason = check_command(cmd)
                self.assertTrue(is_blocked, f"Should block: {cmd}")
                self.assertIn("rm -rf", reason)

    def test_rm_allowed(self):
        allowed_cmds = [
            "rm file.txt",
            "rm -r folder",
            "rm -f single_file.txt",
            "git rm file.txt",
        ]
        for cmd in allowed_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, _ = check_command(cmd)
                self.assertFalse(is_blocked, f"Should allow: {cmd}")

    # 2. DROP TABLE
    def test_drop_table_blocked(self):
        blocked_cmds = [
            "DROP TABLE users;",
            "drop table if exists temp_data;",
            "psql -d app -c 'DROP TABLE customers;'",
        ]
        for cmd in blocked_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, reason = check_command(cmd)
                self.assertTrue(is_blocked, f"Should block: {cmd}")
                self.assertIn("DROP TABLE", reason)

    # 3. git push --force
    def test_git_force_push_blocked(self):
        blocked_cmds = [
            "git push --force",
            "git push -f origin main",
            "git push origin main --force",
            "git push --force-with-lease",
        ]
        for cmd in blocked_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, reason = check_command(cmd)
                self.assertTrue(is_blocked, f"Should block: {cmd}")
                self.assertIn("git push --force", reason)

    def test_git_push_allowed(self):
        allowed_cmds = [
            "git push",
            "git push origin main",
            "git push origin fix/issue-3",
            "git status",
        ]
        for cmd in allowed_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, _ = check_command(cmd)
                self.assertFalse(is_blocked, f"Should allow: {cmd}")

    # 4. TRUNCATE
    def test_truncate_blocked(self):
        blocked_cmds = [
            "TRUNCATE TABLE audit_logs;",
            "truncate table temp;",
            "psql -c 'TRUNCATE logs;'",
        ]
        for cmd in blocked_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, reason = check_command(cmd)
                self.assertTrue(is_blocked, f"Should block: {cmd}")
                self.assertIn("TRUNCATE", reason)

    # 5. DELETE FROM without WHERE
    def test_delete_without_where_blocked(self):
        blocked_cmds = [
            "DELETE FROM users;",
            "delete from customers",
            "DELETE FROM t1; DELETE FROM t2 WHERE id=1;",
        ]
        for cmd in blocked_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, reason = check_command(cmd)
                self.assertTrue(is_blocked, f"Should block: {cmd}")
                self.assertIn("DELETE FROM", reason)

    def test_delete_with_where_allowed(self):
        allowed_cmds = [
            "DELETE FROM users WHERE id = 1;",
            "delete from customers where status = 'inactive'",
            "DELETE FROM orders WHERE created_at < '2020-01-01';",
        ]
        for cmd in allowed_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, _ = check_command(cmd)
                self.assertFalse(is_blocked, f"Should allow: {cmd}")

    # 6. Normal bash commands
    def test_normal_bash_commands(self):
        normal_cmds = [
            "ls -la",
            "mkdir -p src/components",
            "python3 -m unittest discover",
            "npm run build",
            "echo 'Hello World'",
            "cat README.md",
        ]
        for cmd in normal_cmds:
            with self.subTest(cmd=cmd):
                is_blocked, _ = check_command(cmd)
                self.assertFalse(is_blocked, f"Should allow normal command: {cmd}")

    # 7. Logging functionality
    def test_logging(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_file:
            log_path = tmp_file.name

        try:
            log_blocked_attempt("rm -rf /", "/test/project", "rm -rf (recursive force remove)", log_path=log_path)
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("rm -rf /", content)
            self.assertIn("/test/project", content)
            self.assertIn("rm -rf (recursive force remove)", content)
            self.assertIn("Project:", content)
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)


class TestPreToolUseE2E(unittest.TestCase):
    """End-to-End CLI / Subprocess tests."""

    def setUp(self):
        self.script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "hooks", "pre_tool_use.py")
        )

    def test_subprocess_blocked_json_stdin(self):
        payload = {
            "cwd": "/path/to/my_project",
            "tool_name": "Bash",
            "tool_input": {
                "command": "rm -rf /"
            }
        }
        proc = subprocess.run(
            [sys.executable, self.script_path],
            input=json.dumps(payload),
            text=True,
            capture_output=True
        )

        self.assertNotEqual(proc.returncode, 0, "Blocked command must exit non-zero")
        data = json.loads(proc.stdout)
        self.assertEqual(data.get("status"), "blocked")
        self.assertIn("rm -rf", data.get("reason", ""))
        self.assertEqual(data.get("command"), "rm -rf /")
        self.assertEqual(data.get("project_path"), "/path/to/my_project")

    def test_subprocess_allowed_json_stdin(self):
        payload = {
            "cwd": "/path/to/my_project",
            "tool_name": "Bash",
            "tool_input": {
                "command": "ls -la"
            }
        }
        proc = subprocess.run(
            [sys.executable, self.script_path],
            input=json.dumps(payload),
            text=True,
            capture_output=True
        )

        self.assertEqual(proc.returncode, 0, "Normal command must exit 0")
        self.assertEqual(proc.stdout.strip(), "")

    def test_subprocess_blocked_cli_arg(self):
        proc = subprocess.run(
            [sys.executable, self.script_path, "DROP TABLE users;", "/path/to/my_project"],
            capture_output=True,
            text=True
        )

        self.assertNotEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data.get("status"), "blocked")
        self.assertIn("DROP TABLE", data.get("reason", ""))


if __name__ == "__main__":
    unittest.main()
