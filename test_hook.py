import unittest
import os
import sys

sys.path.insert(0, '/tmp/claude-builders-bounty/hooks/pre-tool-use')
from block_destructive_bash import check_command

class TestDestructiveBashHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked, reason = check_command("rm -rf /tmp/data")
        self.assertFalse(blocked)
        self.assertIn("Recursive forced deletion", reason)

        blocked, reason = check_command("rm -fr /tmp/data")
        self.assertFalse(blocked)

    def test_blocks_git_force_push(self):
        blocked, reason = check_command("git push origin main --force")
        self.assertFalse(blocked)
        self.assertIn("Forced git push", reason)

        blocked, reason = check_command("git push -f origin main")
        self.assertFalse(blocked)

    def test_blocks_drop_table(self):
        blocked, reason = check_command("sqlite3 db.sqlite 'DROP TABLE users;'")
        self.assertFalse(blocked)
        self.assertIn("DROP TABLE", reason)

    def test_blocks_truncate(self):
        blocked, reason = check_command("psql -c 'TRUNCATE orders;'")
        self.assertFalse(blocked)
        self.assertIn("TRUNCATE", reason)

    def test_blocks_delete_without_where(self):
        blocked, reason = check_command("sqlite3 db.sqlite 'DELETE FROM users'")
        self.assertFalse(blocked)
        self.assertIn("without a WHERE clause", reason)

    def test_allows_safe_commands(self):
        safe_cmds = [
            "ls -la",
            "git status",
            "python3 -m unittest",
            "cat README.md",
            "sqlite3 db.sqlite 'DELETE FROM users WHERE id = 5;'"
        ]
        for cmd in safe_cmds:
            allowed, _ = check_command(cmd)
            self.assertTrue(allowed, f"Expected '{cmd}' to be allowed")

if __name__ == '__main__':
    unittest.main()
