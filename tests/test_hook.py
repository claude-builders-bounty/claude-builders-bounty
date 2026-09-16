"""
Comprehensive Test Suite for Claude Code Pre-Tool-Use Destructive Command Guard
"""

import os
import tempfile
import subprocess
import unittest
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "hooks" / "block_destructive.py"

class TestBlockDestructiveHook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "blocked.log"
        self.env = os.environ.copy()
        self.env["CLAUDE_HOOK_LOG_PATH"] = str(self.log_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook(self, command_or_json: str):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=command_or_json,
            text=True,
            capture_output=True,
            env=self.env,
        )
        return result

    def test_safe_commands_allowed(self):
        safe_commands = [
            "ls -la",
            "git status",
            "npm run test",
            "pytest tests/",
            "git push origin feat/new-ui",
            "DELETE FROM users WHERE id = 101;",
            "DELETE FROM audit WHERE created_at < NOW() - INTERVAL '30 days';",
            "rm file.txt",
            "echo 'hello world'",
        ]
        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 0, f"Safe command was blocked: {cmd}\nStderr: {res.stderr}")
                self.assertFalse(self.log_path.exists(), f"Log was written for safe command: {cmd}")

    def test_rm_rf_blocked(self):
        dangerous = [
            "rm -rf /var/data",
            "rm -fr ./node_modules",
            "rm -r -f build/",
            "rm --recursive --force dist/",
        ]
        for cmd in dangerous:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 1, f"Dangerous command passed: {cmd}")
                self.assertIn("rm -rf", res.stderr)
                self.assertTrue(self.log_path.exists())

    def test_drop_table_blocked(self):
        res = self.run_hook("DROP TABLE users;")
        self.assertEqual(res.returncode, 1)
        self.assertIn("DROP TABLE", res.stderr)
        self.assertTrue(self.log_path.exists())

    def test_git_push_force_blocked(self):
        force_cmds = [
            "git push origin main --force",
            "git push -f origin main",
            "git push --force-with-lease origin main",
        ]
        for cmd in force_cmds:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 1)
                self.assertIn("git push --force", res.stderr)

    def test_truncate_blocked(self):
        truncate_cmds = [
            "TRUNCATE TABLE sessions;",
            "truncate users",
            "TRUNCATE events;",
        ]
        for cmd in truncate_cmds:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 1)
                self.assertIn("TRUNCATE", res.stderr)

    def test_delete_without_where_blocked(self):
        unconditional_deletes = [
            "DELETE FROM accounts;",
            "delete from sessions",
            "DELETE FROM `orders`;",
        ]
        for cmd in unconditional_deletes:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 1)
                self.assertIn("DELETE FROM without WHERE", res.stderr)

    def test_claude_code_json_payload(self):
        json_payload = '{"tool_name": "bash", "tool_input": {"command": "rm -rf /important"}}'
        res = self.run_hook(json_payload)
        self.assertEqual(res.returncode, 1)
        self.assertIn("rm -rf", res.stderr)
        self.assertTrue(self.log_path.exists())

    def test_non_bash_tool_ignored(self):
        json_payload = '{"tool_name": "view_file", "tool_input": {"path": "rm -rf.txt"}}'
        res = self.run_hook(json_payload)
        self.assertEqual(res.returncode, 0)

if __name__ == "__main__":
    import sys
    unittest.main()
