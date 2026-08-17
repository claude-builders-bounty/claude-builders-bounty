"""
Comprehensive test suite for destructive command hook.
Tests all blocked patterns, safe commands, payload extraction, and log persistence.
"""

import unittest
import os
import sys
import tempfile
import json

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pre_tool_use import inspect_command, extract_command_from_payload, log_blocked_attempt

class TestDestructiveCommandHook(unittest.TestCase):

    def test_blocks_rm_rf_variants(self):
        blocked_commands = [
            "rm -rf /tmp/test",
            "rm -fr ./node_modules",
            "rm -r -f ./build",
            "rm --recursive --force ./dist",
            "sudo rm -rf /var/log/*"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = inspect_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")
            self.assertIn("Recursive force removal", reason)

    def test_blocks_drop_table_and_database(self):
        blocked_commands = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            "DROP DATABASE production",
            "DROP SCHEMA public CASCADE;",
            "DROP VIEW active_users;"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = inspect_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")
            self.assertIn("DROP operations are forbidden", reason)

    def test_blocks_git_force_push(self):
        blocked_commands = [
            "git push origin main --force",
            "git push -f origin master",
            "git push --force-with-lease origin feat",
            "git push -u origin HEAD --force"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = inspect_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")
            self.assertIn("Force-pushing git history", reason)

    def test_blocks_truncate(self):
        blocked_commands = [
            "TRUNCATE TABLE logs;",
            "truncate users",
            "TRUNCATE `sessions`;",
            "TRUNCATE \"audit_trail\""
        ]
        for cmd in blocked_commands:
            is_blocked, reason = inspect_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")
            self.assertIn("TRUNCATE", reason)

    def test_blocks_delete_without_where(self):
        blocked_commands = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM `orders`",
            "echo 'running'; DELETE FROM customers;"
        ]
        for cmd in blocked_commands:
            is_blocked, reason = inspect_command(cmd)
            self.assertTrue(is_blocked, f"Should have blocked: {cmd}")
            self.assertIn("without a WHERE clause", reason)

    def test_allows_safe_commands(self):
        safe_commands = [
            "rm single_file.txt",
            "rm -f individual_cache.tmp",
            "git push origin main",
            "git push -u origin feat/my-branch",
            "npm run test",
            "pnpm build",
            "git status",
            "git log -n 5",
            "DELETE FROM users WHERE id = 42;",
            "DELETE FROM sessions WHERE expires_at < '2026-01-01';",
            "SELECT * FROM users WHERE active = 1;",
            "echo 'DROP TABLE is a concept in SQL'"
        ]
        for cmd in safe_commands:
            is_blocked, reason = inspect_command(cmd)
            self.assertFalse(is_blocked, f"Should NOT have blocked safe command: {cmd} (reason: {reason})")

    def test_extract_command_from_claude_json_payload(self):
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {
                "command": "rm -rf /var/www"
            }
        })
        extracted = extract_command_from_payload(payload)
        self.assertEqual(extracted, "rm -rf /var/www")
        is_blocked, _ = inspect_command(extracted)
        self.assertTrue(is_blocked)

    def test_blocked_logging(self):
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()
        os.environ["BLOCKED_LOG_PATH"] = temp_log.name
        try:
            log_blocked_attempt("rm -rf /test", "Test reason", cwd="/project/app")
            with open(temp_log.name, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("BLOCKED: \"rm -rf /test\"", content)
            self.assertIn("REASON: Test reason", content)
            self.assertIn("PATH: /project/app", content)
        finally:
            if os.path.exists(temp_log.name):
                os.remove(temp_log.name)
            del os.environ["BLOCKED_LOG_PATH"]

if __name__ == "__main__":
    unittest.main(verbosity=2)
