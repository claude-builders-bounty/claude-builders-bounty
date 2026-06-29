#!/usr/bin/env python3
import sys
import os
import unittest

# Add hooks directory to path so we can import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../hooks')))
from pre_tool_use import check_command

class TestPreToolUseHook(unittest.TestCase):
    def test_rm_rf_blocking(self):
        blocked_commands = [
            "rm -rf /",
            "rm -rf ./node_modules",
            "rm -fr some_dir",
            "rm -r -f file",
            "rm -f -r file",
            "rm --recursive --force dir",
            "rm --force --recursive dir",
            "sudo rm -rf /etc"
        ]
        for cmd in blocked_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(check_command(cmd), f"Should have blocked: {cmd}")

    def test_rm_rf_allowing(self):
        allowed_commands = [
            "rm file.txt",
            "rm -f file.txt",
            "rm -r dir",
            "rmdir empty_dir",
            "echo rm -rf"
        ]
        for cmd in allowed_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Should not have blocked: {cmd}")

    def test_drop_blocking(self):
        blocked_commands = [
            "DROP TABLE users;",
            "drop database production;",
            "sqlite3 db.sqlite \"DROP TABLE sessions;\""
        ]
        for cmd in blocked_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(check_command(cmd), f"Should have blocked: {cmd}")

    def test_git_push_force_blocking(self):
        blocked_commands = [
            "git push --force",
            "git push -f",
            "git push origin main --force",
            "git push -f origin main"
        ]
        for cmd in blocked_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(check_command(cmd), f"Should have blocked: {cmd}")

    def test_git_push_force_allowing(self):
        allowed_commands = [
            "git push",
            "git push origin main",
            "git push --force-with-lease",
            "git push --force-if-includes origin main",
            "echo git push -f"
        ]
        for cmd in allowed_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Should not have blocked: {cmd}")

    def test_truncate_blocking(self):
        blocked_commands = [
            "TRUNCATE TABLE logs;",
            "truncate users;"
        ]
        for cmd in blocked_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(check_command(cmd), f"Should have blocked: {cmd}")

    def test_delete_from_blocking(self):
        blocked_commands = [
            "DELETE FROM users;",
            "delete from sessions",
            "DELETE FROM logs\n"
        ]
        for cmd in blocked_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(check_command(cmd), f"Should have blocked: {cmd}")

    def test_delete_from_allowing(self):
        allowed_commands = [
            "DELETE FROM users WHERE id = 1;",
            "delete from sessions where expired = true",
            "DELETE FROM logs WHERE level = 'DEBUG';"
        ]
        for cmd in allowed_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Should not have blocked: {cmd}")

class TestPreToolUseHookCli(unittest.TestCase):
    def run_hook(self, stdin_data):
        import subprocess
        hook_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../hooks/pre_tool_use.py'))
        proc = subprocess.Popen(
            [sys.executable, hook_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input=stdin_data)
        return proc.returncode, stdout, stderr

    def test_cli_blocked_json(self):
        payload = {
            "tool_name": "bash",
            "tool_input": {
                "command": "rm -rf /tmp/test"
            }
        }
        code, stdout, stderr = self.run_hook(json.dumps(payload))
        self.assertEqual(code, 1)
        self.assertIn("hookSpecificOutput", stdout)
        self.assertIn("deny", stdout)
        self.assertIn("blocked by pre-tool-use hook", stderr.lower())

    def test_cli_allowed_json(self):
        payload = {
            "tool_name": "bash",
            "tool_input": {
                "command": "ls -la"
            }
        }
        code, stdout, stderr = self.run_hook(json.dumps(payload))
        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "")

    def test_cli_non_bash_tool_ignored(self):
        payload = {
            "tool_name": "edit",
            "tool_input": {
                "command": "rm -rf /tmp/test"
            }
        }
        code, stdout, stderr = self.run_hook(json.dumps(payload))
        self.assertEqual(code, 0)

    def test_cli_raw_text_input(self):
        code, stdout, stderr = self.run_hook("git push --force")
        self.assertEqual(code, 1)
        self.assertIn("hookSpecificOutput", stdout)

if __name__ == '__main__':
    import json
    unittest.main()
