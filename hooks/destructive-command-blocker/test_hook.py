import unittest
from block_destructive_commands import check_command

class TestDestructiveBlocker(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked, _ = check_command("rm -rf /tmp/test")
        self.assertTrue(blocked)
        blocked2, _ = check_command("rm -fr ./build")
        self.assertTrue(blocked2)

    def test_blocks_force_push(self):
        blocked, _ = check_command("git push origin main --force")
        self.assertTrue(blocked)
        blocked2, _ = check_command("git push -f")
        self.assertTrue(blocked2)

    def test_blocks_sql_drop_truncate(self):
        blocked, _ = check_command('psql -c "DROP TABLE users;"')
        self.assertTrue(blocked)
        blocked2, _ = check_command('mysql -e "TRUNCATE customers"')
        self.assertTrue(blocked2)

    def test_blocks_delete_without_where(self):
        blocked, _ = check_command("DELETE FROM sessions")
        self.assertTrue(blocked)

    def test_allows_safe_commands(self):
        safe_commands = [
            "ls -la",
            "rm file.txt",
            "git push origin feature",
            "SELECT * FROM users",
            "DELETE FROM sessions WHERE expired = 1"
        ]
        for cmd in safe_commands:
            blocked, _ = check_command(cmd)
            self.assertFalse(blocked, f"Safe command incorrectly blocked: {cmd}")

if __name__ == "__main__":
    unittest.main()