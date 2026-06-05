#!/usr/bin/env python3
"""Tests for the pre-tool-use hook — imports functions directly."""

import os
import re
import sys
import unittest

# Import the hook's is_dangerous function directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Import carefully — we only need is_dangerous and PATTERNS

HOOK_PATH = os.path.join(os.path.dirname(__file__), "..", "pre-tool-use.py")
# Read and exec only the function/constant definitions (skip main block)
with open(HOOK_PATH, "r", encoding="utf-8") as f:
    code = f.read()

# Split at main() to avoid executing it; set __file__ for the hook
code = code.split("\nif __name__")[0]
globals()["__file__"] = os.path.abspath(HOOK_PATH)
exec(code, globals())


class TestBlocker(unittest.TestCase):

    # ── Should BLOCK ─────────────────────────────────────────────────────
    def test_rm_rf(self):
        for cmd in ["rm -rf /tmp", "rm -rf /", "rm --recursive --force /x"]:
            d, r = is_dangerous(cmd)
            self.assertTrue(d, f"Should block: {cmd}")

    def test_drop(self):
        for cmd in ["DROP TABLE users", "drop table if exists x", "DROP DATABASE prod"]:
            d, r = is_dangerous(cmd)
            self.assertTrue(d, f"Should block: {cmd}")

    def test_git_push_force(self):
        for cmd in ["git push --force origin main", "git push -f"]:
            d, r = is_dangerous(cmd)
            self.assertTrue(d, f"Should block: {cmd}")

    def test_truncate(self):
        for cmd in ["TRUNCATE TABLE logs", "truncate table x"]:
            d, r = is_dangerous(cmd)
            self.assertTrue(d, f"Should block: {cmd}")

    def test_delete_from_no_where(self):
        d, r = is_dangerous("DELETE FROM users")
        self.assertTrue(d)

    def test_chmod_777(self):
        d, r = is_dangerous("chmod -R 777 /var/www")
        self.assertTrue(d)

    # ── Should ALLOW ─────────────────────────────────────────────────────
    def test_safe_commands(self):
        safe = [
            "ls -la /tmp",
            "echo hello",
            "git push origin main",
            "git push --force-with-lease",
            "rm file.txt",
            "python script.py",
            "DELETE FROM users WHERE id = 1",
            "cat /etc/passwd",
            "npm install",
            "pip install requests",
            "SELECT * FROM users",
        ]
        for cmd in safe:
            d, r = is_dangerous(cmd)
            self.assertFalse(d, f"Should allow: {cmd}  (reason: {r})")

    def test_non_bash_not_checked(self):
        """is_dangerous doesn't check tool type — that's handled in main()"""
        # The tool-filtering is done in main(), not is_dangerous
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
