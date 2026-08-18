#!/usr/bin/env python3
"""Tests for hooks/pre_tool_use.py

Run with:
    python -m unittest discover -s tests -v
"""

import json
import os
import sys
import unittest
from unittest import mock

_HOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from hooks.pre_tool_use import (
    check_command,
    handle_event,
    log_blocked,
    _get_log_path,
    _get_log_dir,
)


def _bash_event(command):
    """Build a minimal Bash tool event dict (official Claude Code format)."""
    return {
        "tool_name": "bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/test-project",
    }


def _bash_event_legacy(command):
    """Build a Bash event using legacy arguments field."""
    return {
        "tool_name": "bash",
        "arguments": {"command": command},
        "project_path": "/tmp/test-project",
    }


def _non_bash_event():
    return {
        "tool_name": "Read",
        "arguments": {"file": "foo.txt"},
    }


class TestBlockedCommands(unittest.TestCase):
    """Commands that MUST be blocked."""

    def test_rm_rf_slash(self):
        blocked, reason = check_command("rm -rf /")
        self.assertTrue(blocked)
        self.assertIsNotNone(reason)

    def test_rm_rf_directory(self):
        blocked, reason = check_command("rm -rf some_directory")
        self.assertTrue(blocked)

    def test_rm_fr_reverse_flags(self):
        blocked, reason = check_command("rm -fr /tmp/data")
        self.assertTrue(blocked)

    def test_rm_r_f_separate_flags(self):
        blocked, reason = check_command("rm -r -f /tmp/x")
        self.assertTrue(blocked)

    def test_rm_f_r_separate_flags(self):
        blocked, reason = check_command("rm -f -r /tmp/x")
        self.assertTrue(blocked)

    def test_sudo_rm_rf(self):
        blocked, reason = check_command("sudo rm -rf /tmp/x")
        self.assertTrue(blocked)

    def test_drop_table_upper(self):
        blocked, reason = check_command("DROP TABLE users")
        self.assertTrue(blocked)

    def test_drop_table_lower(self):
        blocked, reason = check_command("drop table users")
        self.assertTrue(blocked)

    def test_git_push_force_long(self):
        blocked, reason = check_command("git push --force origin main")
        self.assertTrue(blocked)

    def test_git_push_force_after_refspec(self):
        blocked, reason = check_command("git push origin main --force")
        self.assertTrue(blocked)

    def test_git_push_force_short(self):
        blocked, reason = check_command("git push -f origin main")
        self.assertTrue(blocked)

    def test_git_push_f_after_refspec(self):
        blocked, reason = check_command("git push origin main -f")
        self.assertTrue(blocked)

    def test_truncate_table(self):
        blocked, reason = check_command("TRUNCATE TABLE users")
        self.assertTrue(blocked)

    def test_truncate_no_table_keyword(self):
        blocked, reason = check_command("TRUNCATE users")
        self.assertTrue(blocked)

    def test_delete_from_no_where(self):
        blocked, reason = check_command("DELETE FROM users")
        self.assertTrue(blocked)

    def test_delete_from_no_where_semicolon(self):
        blocked, reason = check_command("DELETE FROM users;")
        self.assertTrue(blocked)

    def test_delete_from_multi_statement(self):
        blocked, reason = check_command("DELETE FROM users; DELETE FROM orders")
        self.assertTrue(blocked)

    def test_truncate_via_psql(self):
        blocked, reason = check_command('psql -c "TRUNCATE TABLE logs"')
        self.assertTrue(blocked)

    def test_truncate_via_psql_no_table_kw(self):
        blocked, reason = check_command('psql -c "TRUNCATE users"')
        self.assertTrue(blocked)

    def test_truncate_via_mysql(self):
        blocked, reason = check_command('mysql -e "TRUNCATE TABLE logs"')
        self.assertTrue(blocked)


class TestAllowedCommands(unittest.TestCase):
    """Commands that MUST be allowed."""

    def test_rm_single_file(self):
        blocked, reason = check_command("rm file.txt")
        self.assertFalse(blocked)

    def test_git_push_normal(self):
        blocked, reason = check_command("git push origin main")
        self.assertFalse(blocked)

    def test_select(self):
        blocked, reason = check_command("SELECT * FROM users")
        self.assertFalse(blocked)

    def test_delete_with_where_id(self):
        blocked, reason = check_command("DELETE FROM users WHERE id = 1")
        self.assertFalse(blocked)

    def test_delete_with_where_email(self):
        blocked, reason = check_command("DELETE FROM users where email = 'x@example.com'")
        self.assertFalse(blocked)

    def test_truncate_in_harmless_text(self):
        blocked, reason = check_command("echo 'I need to truncate this string'")
        self.assertFalse(blocked)

    def test_truncate_echo_double_quote(self):
        blocked, reason = check_command('echo "truncate the data"')
        self.assertFalse(blocked)

    def test_truncate_echo_prose(self):
        blocked, reason = check_command('echo "please truncate the table"')
        self.assertFalse(blocked)

    def test_non_bash_event(self):
        exit_code, response = handle_event(_non_bash_event())
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            response["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_git_push_force_with_lease(self):
        blocked, reason = check_command("git push --force-with-lease origin main")
        self.assertFalse(blocked)

    def test_psql_drop_table(self):
        blocked, reason = check_command('psql -c "DROP TABLE users"')
        self.assertTrue(blocked)


class TestHandleEvent(unittest.TestCase):
    """Integration tests for handle_event."""

    def test_blocked_event_returns_deny(self):
        with mock.patch('hooks.pre_tool_use.log_blocked'):
            exit_code, response = handle_event(_bash_event("rm -rf /"))
        self.assertEqual(exit_code, 2)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "deny")
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        self.assertIn("permissionDecisionReason", hso)

    def test_safe_event_allows(self):
        exit_code, response = handle_event(_bash_event("echo hello"))
        self.assertEqual(exit_code, 0)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "allow")

    def test_non_bash_passes_through(self):
        exit_code, response = handle_event(_non_bash_event())
        self.assertEqual(exit_code, 0)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "allow")

    def test_malformed_input_allows(self):
        exit_code, response = handle_event({})
        self.assertEqual(exit_code, 0)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "allow")

    def test_missing_command_allows(self):
        exit_code, response = handle_event({"tool_name": "bash", "tool_input": {}})
        self.assertEqual(exit_code, 0)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "allow")

    def test_legacy_arguments_field(self):
        exit_code, response = handle_event(_bash_event_legacy("echo hello"))
        self.assertEqual(exit_code, 0)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "allow")

    def test_legacy_arguments_blocked(self):
        with mock.patch('hooks.pre_tool_use.log_blocked'):
            exit_code, response = handle_event(_bash_event_legacy("rm -rf /"))
        self.assertEqual(exit_code, 2)
        hso = response["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "deny")


class TestLogging(unittest.TestCase):
    """Logging tests that do NOT write to the real user log."""

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('hooks.pre_tool_use._get_log_path', return_value='/tmp/fake/blocked.log')
    @mock.patch('hooks.pre_tool_use._get_log_dir', return_value='/tmp/fake')
    def test_log_blocked_writes_entry(self, mock_dir, mock_path, mock_open_fn):
        log_blocked('rm -rf /', '/tmp/test-project')
        mock_open_fn.assert_called_once_with('/tmp/fake/blocked.log', 'a', encoding='utf-8')
        handle = mock_open_fn()
        self.assertTrue(handle.write.called)
        written = handle.write.call_args[0][0]
        self.assertIn('rm -rf /', written)
        self.assertIn('BLOCKED', written)

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('hooks.pre_tool_use._get_log_path', return_value='/tmp/fake/blocked.log')
    @mock.patch('hooks.pre_tool_use._get_log_dir', return_value='/tmp/fake')
    @mock.patch('os.makedirs')
    def test_log_blocked_creates_dir(self, mock_makedirs, mock_path, mock_dir, mock_open_fn):
        log_blocked('rm -rf /')
        mock_makedirs.assert_called()


if __name__ == '__main__':
    unittest.main()
