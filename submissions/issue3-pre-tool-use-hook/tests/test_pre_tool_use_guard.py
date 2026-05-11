#!/usr/bin/env python3
"""Tests for pre_tool_use_guard.py"""
import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pre_tool_use_guard import check_command


class TestDestructivePatterns(unittest.TestCase):
    # --- should block ---
    def test_rm_rf(self):
        blocked, reason = check_command("rm -rf /tmp/foo")
        self.assertTrue(blocked)
        self.assertIn("recursive force", reason)

    def test_rm_fr(self):
        blocked, _ = check_command("rm -fr ./build")
        self.assertTrue(blocked)

    def test_rm_rf_with_flags(self):
        blocked, _ = check_command("rm -rf --no-preserve-root /")
        self.assertTrue(blocked)

    def test_drop_table(self):
        blocked, _ = check_command("DROP TABLE users;")
        self.assertTrue(blocked)

    def test_drop_table_lowercase(self):
        blocked, _ = check_command("drop table sessions;")
        self.assertTrue(blocked)

    def test_truncate(self):
        blocked, _ = check_command("TRUNCATE orders;")
        self.assertTrue(blocked)

    def test_delete_without_where(self):
        blocked, _ = check_command("DELETE FROM logs;")
        self.assertTrue(blocked)

    def test_git_push_force(self):
        blocked, _ = check_command("git push origin main --force")
        self.assertTrue(blocked)

    def test_git_push_f(self):
        blocked, _ = check_command("git push -f origin main")
        self.assertTrue(blocked)

    # --- should allow ---
    def test_safe_rm(self):
        blocked, _ = check_command("rm -f /tmp/specific_file.txt")
        self.assertFalse(blocked)

    def test_safe_delete_with_where(self):
        blocked, _ = check_command("DELETE FROM logs WHERE created_at < '2020-01-01';")
        self.assertFalse(blocked)

    def test_safe_git_push(self):
        blocked, _ = check_command("git push origin feature-branch")
        self.assertFalse(blocked)

    def test_safe_ls(self):
        blocked, _ = check_command("ls -la")
        self.assertFalse(blocked)

    def test_safe_grep(self):
        blocked, _ = check_command("grep -r 'DROP TABLE' .")
        self.assertFalse(blocked)

    def test_empty_command(self):
        blocked, _ = check_command("")
        self.assertFalse(blocked)


if __name__ == "__main__":
    unittest.main()
