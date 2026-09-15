import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from guard import check_command

class TestSecurityHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        cases = [
            "rm -rf /tmp/data",
            "rm -fr ./build",
            "rm -r -f *",
            "sudo rm -rf /var/log",
            "rm --recursive --force node_modules"
        ]
        for cmd in cases:
            safe, reason = check_command(cmd)
            self.assertFalse(safe, f"Failed to block: {cmd}")
            self.assertIn("rm -rf", reason)

    def test_blocks_drop_table(self):
        cases = [
            "psql -c 'DROP TABLE users;'",
            "mysql -e 'drop table accounts;'",
            "DROP TABLE IF EXISTS sessions;"
        ]
        for cmd in cases:
            safe, reason = check_command(cmd)
            self.assertFalse(safe, f"Failed to block: {cmd}")
            self.assertIn("DROP TABLE", reason)

    def test_blocks_truncate(self):
        cases = [
            "TRUNCATE TABLE logs;",
            "truncate audit_events",
            "TRUNCATE `orders`"
        ]
        for cmd in cases:
            safe, reason = check_command(cmd)
            self.assertFalse(safe, f"Failed to block: {cmd}")
            self.assertIn("TRUNCATE", reason)

    def test_blocks_git_push_force(self):
        cases = [
            "git push origin main --force",
            "git push -f",
            "git push origin head --force-with-lease"
        ]
        for cmd in cases:
            safe, reason = check_command(cmd)
            self.assertFalse(safe, f"Failed to block: {cmd}")
            self.assertIn("git push --force", reason)

    def test_blocks_delete_without_where(self):
        cases = [
            "DELETE FROM users;",
            "delete from accounts",
            "sqlite3 app.db 'DELETE FROM sessions;'"
        ]
        for cmd in cases:
            safe, reason = check_command(cmd)
            self.assertFalse(safe, f"Failed to block: {cmd}")
            self.assertIn("DELETE FROM", reason)

    def test_allows_safe_commands(self):
        safe_cases = [
            "ls -la",
            "git status",
            "git push origin feature-branch",
            "DELETE FROM users WHERE id = 123",
            "npm test",
            "python build.py",
            "rm safe_file.txt",
            "cat README.md"
        ]
        for cmd in safe_cases:
            safe, _ = check_command(cmd)
            self.assertTrue(safe, f"Wrongly blocked safe command: {cmd}")

if __name__ == '__main__':
    unittest.main()
