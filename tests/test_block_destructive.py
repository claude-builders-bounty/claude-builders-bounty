"""
Unit test suite verifying that the Claude Code Destructive Command Interceptor
satisfies all specifications and acceptance criteria of Bounty #3.
Zero external dependencies (uses standard library unittest).
"""

import os
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from block_destructive import (
    check_command,
    extract_command_from_payload,
    log_blocked_attempt,
)


class TestBlockDestructiveHook(unittest.TestCase):
    def test_rm_rf_blocked(self):
        """Verify rm -rf variations are blocked."""
        blocked_commands = [
            "rm -rf /var/data",
            "rm -fr ./temp",
            "rm -r -f build/",
            "rm --recursive --force dist/",
            "sudo rm -rf /",
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("rm -rf", reason)

    def test_safe_rm_allowed(self):
        """Verify safe non-recursive rm operations are allowed."""
        safe_commands = [
            "rm test.txt",
            "rm -i old.log",
            "rm file1.js file2.js",
        ]
        for cmd in safe_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Expected '{cmd}' to be allowed.")

    def test_drop_table_blocked(self):
        """Verify DROP TABLE statements are blocked."""
        blocked_commands = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            'sqlite3 db.sqlite "DROP TABLE sessions;"',
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("DROP TABLE", reason)

    def test_git_push_force_blocked(self):
        """Verify git force pushes are blocked."""
        blocked_commands = [
            "git push --force origin main",
            "git push origin master -f",
            "git push origin +feature/branch",
            "git push --force",
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("git push --force", reason)

    def test_safe_git_push_allowed(self):
        """Verify standard git push operations are allowed."""
        safe_commands = [
            "git push origin main",
            "git push",
            "git push -u origin feat/my-branch",
            "git status",
            "git commit -m 'feat: update code'",
        ]
        for cmd in safe_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Expected '{cmd}' to be allowed.")

    def test_truncate_blocked(self):
        """Verify TRUNCATE statements are blocked."""
        blocked_commands = [
            "TRUNCATE TABLE logs;",
            "truncate users",
            'psql -c "TRUNCATE TABLE transactions;"',
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("TRUNCATE", reason)

    def test_delete_without_where_blocked(self):
        """Verify DELETE FROM without WHERE is blocked."""
        blocked_commands = [
            "DELETE FROM users;",
            "DELETE FROM accounts",
            'sqlite3 db.db "delete from sessions;"',
        ]
        for cmd in blocked_commands:
            is_blocked, reason = check_command(cmd)
            self.assertTrue(is_blocked, f"Expected '{cmd}' to be blocked.")
            self.assertIn("DELETE FROM", reason)

    def test_delete_with_where_allowed(self):
        """Verify DELETE FROM with WHERE clause is permitted."""
        safe_commands = [
            "DELETE FROM users WHERE id = 42;",
            "delete from sessions where expires_at < NOW()",
            'sqlite3 db.db "DELETE FROM cache WHERE key = \'temp\';"',
        ]
        for cmd in safe_commands:
            is_blocked, _ = check_command(cmd)
            self.assertFalse(is_blocked, f"Expected '{cmd}' to be allowed.")

    def test_payload_extraction(self):
        """Verify JSON payload parsing from Claude Code hook format."""
        json_payload = '{"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}'
        cmd = extract_command_from_payload(json_payload)
        self.assertEqual(cmd, "git push --force origin main")

        raw_cmd = "npm run test"
        self.assertEqual(extract_command_from_payload(raw_cmd), "npm run test")

    def test_logging_behavior(self):
        """Verify blocked attempts write to log file with timestamp, project, and command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_log = Path(temp_dir) / "test_blocked.log"
            log_blocked_attempt(
                command="rm -rf /tmp/data",
                project_path="/home/user/project",
                reason="rm -rf",
                log_file=temp_log,
            )
            self.assertTrue(temp_log.exists())
            content = temp_log.read_text(encoding="utf-8")
            self.assertIn("[BLOCKED]", content)
            self.assertIn("/home/user/project", content)
            self.assertIn("rm -rf /tmp/data", content)


if __name__ == "__main__":
    unittest.main()
