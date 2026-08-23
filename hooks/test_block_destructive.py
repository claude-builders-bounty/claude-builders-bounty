#!/usr/bin/env python3
"""Tests for block_destructive.py pre-tool-use hook (bounty #3, $100)."""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_destructive import check_command

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block_destructive.py")


class TestCheckCommand(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertTrue(check_command("rm -rf /tmp/foo")[0])
        self.assertTrue(check_command("rm -rf --no-preserve-root /")[0])
        self.assertTrue(check_command("rm -fr /tmp/x")[0])
        self.assertTrue(check_command("sudo rm -rf /etc")[0])

    def test_blocks_drop_table(self):
        self.assertTrue(check_command("DROP TABLE users;")[0])
        self.assertTrue(check_command("drop table if exists logs")[0])

    def test_blocks_truncate(self):
        self.assertTrue(check_command("TRUNCATE TABLE audit;")[0])

    def test_blocks_git_push_force(self):
        self.assertTrue(check_command("git push --force origin main")[0])
        self.assertTrue(check_command("git push -f")[0])

    def test_blocks_delete_without_where(self):
        self.assertTrue(check_command("DELETE FROM users;")[0])
        self.assertTrue(check_command("delete from orders")[0])

    def test_allows_delete_with_where(self):
        self.assertFalse(check_command("DELETE FROM users WHERE id = 5;")[0])

    def test_allows_normal_commands(self):
        for cmd in [
            "ls -la",
            "git push origin main",
            "git status",
            "rm file.txt",          # plain rm without -r/-f is allowed
            "pip install requests",
            "SELECT * FROM users",
            "git push --force-with-lease origin main",
        ]:
            self.assertFalse(check_command(cmd)[0], f"should allow: {cmd}")

    def test_allows_safe_echo(self):
        self.assertFalse(check_command('echo "rm -rf /"')[0])
        self.assertFalse(check_command("# rm -rf /")[0])

    def test_empty(self):
        self.assertFalse(check_command("")[0])
        self.assertFalse(check_command(None)[0])


class TestHookBinary(unittest.TestCase):
    def test_hook_blocks_via_json_stdin(self):
        payload = '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"}}'
        p = subprocess.run([sys.executable, HOOK], input=payload,
                           capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(p.returncode, 2)
        self.assertIn("BLOCKED", p.stdout)

    def test_hook_allows_safe_via_json_stdin(self):
        payload = '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'
        p = subprocess.run([sys.executable, HOOK], input=payload,
                           capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(p.returncode, 0)

    def test_log_created_on_block(self):
        log = os.path.expanduser("~/.claude/hooks/blocked.log")
        if os.path.exists(log):
            os.remove(log)
        payload = '{"tool_name":"Bash","tool_input":{"command":"DROP TABLE x;"}}'
        subprocess.run([sys.executable, HOOK], input=payload,
                       capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertTrue(os.path.exists(log))
        with open(log, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("DROP TABLE", content)
        self.assertRegex(content, r"\d{4}-\d{2}-\d{2}")  # timestamp present


if __name__ == "__main__":
    unittest.main(verbosity=2)