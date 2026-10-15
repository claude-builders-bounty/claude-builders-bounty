#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HOOK_SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "block_destructive.py"

class TestBlockDestructiveHook(unittest.TestCase):
    def run_hook(self, command: str, cwd: str = "/tmp/test-project"):
        payload = json.dumps({
            "session_id": "test-session",
            "cwd": cwd,
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command}
        })
        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=payload,
            text=True,
            capture_output=True
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_blocks_rm_rf(self):
        code, stdout, stderr = self.run_hook("rm -rf /")
        self.assertEqual(code, 2)
        self.assertIn("rm -rf", stderr)

    def test_blocks_drop_table(self):
        code, stdout, stderr = self.run_hook("psql -c 'DROP TABLE accounts;'")
        self.assertEqual(code, 2)
        self.assertIn("DROP TABLE", stderr)

    def test_blocks_git_push_force(self):
        code, stdout, stderr = self.run_hook("git push origin main --force")
        self.assertEqual(code, 2)
        self.assertIn("git push --force", stderr)

    def test_blocks_truncate(self):
        code, stdout, stderr = self.run_hook("TRUNCATE TABLE users;")
        self.assertEqual(code, 2)
        self.assertIn("TRUNCATE", stderr)

    def test_blocks_delete_without_where(self):
        code, stdout, stderr = self.run_hook("DELETE FROM sessions;")
        self.assertEqual(code, 2)
        self.assertIn("without WHERE clause", stderr)

    def test_allows_delete_with_where(self):
        code, stdout, stderr = self.run_hook("DELETE FROM sessions WHERE id = 123;")
        self.assertEqual(code, 0)

    def test_allows_safe_commands(self):
        code, stdout, stderr = self.run_hook("git status")
        self.assertEqual(code, 0)
        code, stdout, stderr = self.run_hook("ls -la")
        self.assertEqual(code, 0)
        code, stdout, stderr = self.run_hook("npm run test")
        self.assertEqual(code, 0)

    def test_log_file_written(self):
        self.run_hook("rm -rf ./cache", cwd="/tmp/phoenix_project")
        log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_file.exists())
        with open(log_file, "r") as f:
            content = f.read()
        self.assertIn("/tmp/phoenix_project", content)
        self.assertIn("rm -rf ./cache", content)

if __name__ == "__main__":
    unittest.main()
