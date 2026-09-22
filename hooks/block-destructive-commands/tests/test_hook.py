"""
test_hook.py - Test suite for pre-tool-use command security hook
"""

import os
import sys
import unittest
from pathlib import Path

# Add hook folder to sys.path
hook_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hook_dir))

from importlib import import_module
pre_tool_use = import_module("pre-tool-use")
inspect_command = pre_tool_use.inspect_command
process_hook_input = pre_tool_use.process_hook_input


class TestDestructiveCommandsHook(unittest.TestCase):

    def test_blocks_rm_rf(self):
        blocked_commands = [
            "rm -rf /",
            "rm -rf .",
            "rm -r -f node_modules",
            "rm -rf *",
            "rm --recursive --force build/",
            "sudo rm -fr /var/log",
        ]
        for cmd in blocked_commands:
            blocked, reason = inspect_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")

    def test_blocks_drop_table(self):
        blocked_commands = [
            "DROP TABLE users;",
            "sqlite3 app.db 'drop table accounts'",
            "psql -d test -c 'DROP TABLE subscriptions CASCADE;'",
        ]
        for cmd in blocked_commands:
            blocked, reason = inspect_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")

    def test_blocks_git_push_force(self):
        blocked_commands = [
            "git push origin main --force",
            "git push -f origin main",
            "git push --force-with-lease",
            "git push origin +feature:main",
        ]
        for cmd in blocked_commands:
            blocked, reason = inspect_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")

    def test_blocks_truncate(self):
        blocked_commands = [
            "TRUNCATE users;",
            "TRUNCATE TABLE logs;",
            "sqlite3 db.sqlite 'truncate table audits'",
        ]
        for cmd in blocked_commands:
            blocked, reason = inspect_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")

    def test_blocks_delete_without_where(self):
        blocked_commands = [
            "DELETE FROM users;",
            "sqlite3 db.sqlite 'DELETE FROM accounts;'",
            "DELETE FROM sessions",
        ]
        for cmd in blocked_commands:
            blocked, reason = inspect_command(cmd)
            self.assertTrue(blocked, f"Expected '{cmd}' to be blocked.")

    def test_allows_delete_with_where(self):
        safe_commands = [
            "DELETE FROM users WHERE id = '123';",
            "DELETE FROM sessions WHERE expires_at < NOW();",
        ]
        for cmd in safe_commands:
            blocked, reason = inspect_command(cmd)
            self.assertFalse(blocked, f"Expected safe command '{cmd}' to be allowed.")

    def test_allows_safe_bash_commands(self):
        safe_commands = [
            "git status",
            "git push origin feature/test",
            "npm run test",
            "pnpm build",
            "ls -la",
            "cat README.md",
            "mkdir -p src/components",
            "rm temp.txt",
            "rm -f single_file.log",
        ]
        for cmd in safe_commands:
            blocked, reason = inspect_command(cmd)
            self.assertFalse(blocked, f"Expected safe command '{cmd}' to be allowed.")

    def test_json_payload_handling(self):
        json_payload = '{"tool_name": "bash", "tool_input": {"command": "rm -rf /tmp/data"}, "cwd": "/test"}'
        exit_code = process_hook_input(json_payload)
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
