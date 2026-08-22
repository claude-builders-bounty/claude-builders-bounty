import unittest
from hooks.block_destructive import check_command

class TestDestructiveHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked, _ = check_command("rm -rf /var/data")
        self.assertTrue(blocked)
        blocked, _ = check_command("rm -r /tmp/dir")
        self.assertTrue(blocked)
        blocked, _ = check_command("rm --recursive folder")
        self.assertTrue(blocked)

    def test_blocks_drop_table(self):
        blocked, _ = check_command("DROP TABLE users;")
        self.assertTrue(blocked)
        blocked, _ = check_command("drop database production;")
        self.assertTrue(blocked)

    def test_blocks_git_force_push(self):
        blocked, _ = check_command("git push origin main --force")
        self.assertTrue(blocked)
        blocked, _ = check_command("git push -f origin master")
        self.assertTrue(blocked)

    def test_blocks_truncate(self):
        blocked, _ = check_command("TRUNCATE TABLE sessions;")
        self.assertTrue(blocked)
        blocked, _ = check_command("truncate logs;")
        self.assertTrue(blocked)

    def test_blocks_delete_without_where(self):
        blocked, _ = check_command("DELETE FROM users;")
        self.assertTrue(blocked)

    def test_allows_safe_commands(self):
        blocked, _ = check_command("ls -la")
        self.assertFalse(blocked)
        blocked, _ = check_command("git push origin feature-branch")
        self.assertFalse(blocked)
        blocked, _ = check_command("git status")
        self.assertFalse(blocked)
        blocked, _ = check_command("DELETE FROM users WHERE id = 5;")
        self.assertFalse(blocked)

if __name__ == "__main__":
    unittest.main()
