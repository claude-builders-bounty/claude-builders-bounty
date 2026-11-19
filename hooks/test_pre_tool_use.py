#!/usr/bin/env python3
import unittest
import importlib.util
import os

spec = importlib.util.spec_from_file_location("hook", os.path.join(os.path.dirname(__file__), "pre-tool-use.py"))
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

class TestPreToolUseHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        allowed, _ = hook.check_command("rm -rf /tmp/data", "/repo")
        self.assertFalse(allowed)

    def test_blocks_drop_table(self):
        allowed, _ = hook.check_command("sqlite3 db.sqlite 'DROP TABLE users;'", "/repo")
        self.assertFalse(allowed)

    def test_blocks_git_push_force(self):
        allowed, _ = hook.check_command("git push origin main --force", "/repo")
        self.assertFalse(allowed)

    def test_blocks_truncate(self):
        allowed, _ = hook.check_command("TRUNCATE TABLE logs;", "/repo")
        self.assertFalse(allowed)

    def test_blocks_delete_without_where(self):
        allowed, _ = hook.check_command("DELETE FROM sessions;", "/repo")
        self.assertFalse(allowed)

    def test_allows_safe_delete_with_where(self):
        allowed, _ = hook.check_command("DELETE FROM sessions WHERE expired = 1;", "/repo")
        self.assertTrue(allowed)

    def test_allows_normal_commands(self):
        for cmd in ["npm install", "git status", "ls -la", "python test.py"]:
            allowed, _ = hook.check_command(cmd, "/repo")
            self.assertTrue(allowed)

if __name__ == "__main__":
    unittest.main()
