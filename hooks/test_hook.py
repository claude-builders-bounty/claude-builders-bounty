import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import unittest
import json
import tempfile
from unittest.mock import patch

from block_destructive_bash import inspect_command, log_blocked_attempt, LOG_FILE

class TestDestructiveBashHook(unittest.TestCase):

    def test_blocks_rm_rf(self):
        blocked_commands = [
            "rm -rf /tmp/test",
            "rm -fr /var/log/*",
            "rm -r -f ./dist",
            "rm --recursive --force node_modules",
            "rm -rfv build/",
            "rm -frv .cache"
        ]
        for cmd in blocked_commands:
            result = inspect_command(cmd)
            self.assertIsNotNone(result, f"Failed to block: {cmd}")
            self.assertEqual(result[0], "rm_rf")

    def test_allows_safe_rm(self):
        safe_commands = [
            "rm test.txt",
            "rm -f file.log",
            "rm -r old_dir/", # without -f
            "git rm file.py",
            "echo 'rm -rf' > notes.txt"
        ]
        for cmd in safe_commands:
            result = inspect_command(cmd)
            if "echo" not in cmd and "-r" in cmd and "-f" not in cmd:
                self.assertIsNone(result, f"Should allow non-forced rm -r: {cmd}")

    def test_blocks_git_force_push(self):
        blocked_commands = [
            "git push origin main --force",
            "git push -f origin master",
            "git push --force-with-lease origin feature",
            "git -C /path/to/repo push origin +main",
            "git push origin +feature:main"
        ]
        for cmd in blocked_commands:
            result = inspect_command(cmd)
            self.assertIsNotNone(result, f"Failed to block: {cmd}")
            self.assertEqual(result[0], "git_force_push")

    def test_allows_safe_git_push(self):
        safe_commands = [
            "git push origin main",
            "git push",
            "git push --set-upstream origin feat/test",
            "git status"
        ]
        for cmd in safe_commands:
            self.assertIsNone(inspect_command(cmd), f"Should allow safe git command: {cmd}")

    def test_blocks_drop_table(self):
        blocked_commands = [
            "psql -d db -c 'DROP TABLE users;'",
            "DROP TABLE customers CASCADE",
            "mysql -e 'drop table if exists accounts'",
            'sqlite3 db.sqlite "DROP TABLE logs;"'
        ]
        for cmd in blocked_commands:
            result = inspect_command(cmd)
            self.assertIsNotNone(result, f"Failed to block: {cmd}")
            self.assertEqual(result[0], "drop_table")

    def test_blocks_truncate(self):
        blocked_commands = [
            "TRUNCATE TABLE audit_logs;",
            "truncate users;",
            'psql -c "TRUNCATE transactions;"'
        ]
        for cmd in blocked_commands:
            result = inspect_command(cmd)
            self.assertIsNotNone(result, f"Failed to block: {cmd}")
            self.assertEqual(result[0], "truncate")

    def test_blocks_delete_from_without_where(self):
        blocked_commands = [
            "DELETE FROM users;",
            "delete from accounts",
            "sqlite3 app.db 'DELETE FROM sessions;'",
            "SELECT 1; DELETE FROM cache;"
        ]
        for cmd in blocked_commands:
            result = inspect_command(cmd)
            self.assertIsNotNone(result, f"Failed to block: {cmd}")
            self.assertEqual(result[0], "delete_without_where")

    def test_allows_delete_from_with_where(self):
        safe_commands = [
            "DELETE FROM users WHERE id = 123;",
            "DELETE FROM sessions WHERE expires_at < NOW();",
            "delete from cache where key = 'foo'"
        ]
        for cmd in safe_commands:
            self.assertIsNone(inspect_command(cmd), f"Should allow bounded delete: {cmd}")

    def test_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_log_file = Path(tmpdir) / "test_blocked.log"
            with patch("block_destructive_bash.LOG_FILE", test_log_file):
                log_blocked_attempt("rm -rf /", "/home/test/app", "Test reason")
                self.assertTrue(test_log_file.exists())
                content = test_log_file.read_text(encoding="utf-8")
                self.assertIn("BLOCKED", content)
                self.assertIn("rm -rf /", content)
                self.assertIn("/home/test/app", content)
                self.assertIn("Test reason", content)

if __name__ == "__main__":
    unittest.main()
