#!/usr/bin/env python3
"""
Tests for block_hook.py
Bounty: claude-builders-bounty/claude-builders-bounty #3
"""

import unittest
import sys
import json
from io import StringIO
from pathlib import Path

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent))
from block_hook import check_command, Severity


class TestBlockHook(unittest.TestCase):
    """Test cases for block_hook.py"""

    def test_rm_rf_root_blocked(self):
        """Test rm -rf / is blocked"""
        is_blocked, reason, severity = check_command("rm -rf /")
        self.assertTrue(is_blocked)
        self.assertEqual(severity, Severity.CRITICAL)

    def test_rm_rf_home_blocked(self):
        """Test rm -rf ~ is blocked"""
        is_blocked, reason, severity = check_command("rm -rf ~")
        self.assertTrue(is_blocked)

    def test_drop_table_blocked(self):
        """Test DROP TABLE is blocked"""
        is_blocked, reason, severity = check_command("DROP TABLE users")
        self.assertTrue(is_blocked)
        self.assertEqual(severity, Severity.CRITICAL)

    def test_truncate_blocked(self):
        """Test TRUNCATE is blocked"""
        is_blocked, reason, severity = check_command("TRUNCATE orders")
        self.assertTrue(is_blocked)

    def test_git_push_force_blocked(self):
        """Test git push --force is blocked"""
        is_blocked, reason, severity = check_command("git push --force origin main")
        self.assertTrue(is_blocked)
        self.assertEqual(severity, Severity.HIGH)

    def test_git_push_f_blocked(self):
        """Test git push -f is blocked"""
        is_blocked, reason, severity = check_command("git push -f origin main")
        self.assertTrue(is_blocked)

    def test_safe_ls_allowed(self):
        """Test safe commands are allowed"""
        is_blocked, reason, severity = check_command("ls -la")
        self.assertFalse(is_blocked)

    def test_safe_git_allowed(self):
        """Test safe git commands are allowed"""
        is_blocked, reason, severity = check_command("git status")
        self.assertFalse(is_blocked)

    def test_delete_without_where_blocked(self):
        """Test DELETE without WHERE is blocked"""
        is_blocked, reason, severity = check_command("DELETE FROM users WHERE 1=1")
        self.assertTrue(is_blocked)


if __name__ == '__main__':
    unittest.main()
