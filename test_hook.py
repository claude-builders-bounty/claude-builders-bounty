import unittest
from block_destructive_commands import is_dangerous

class TestHookRules(unittest.TestCase):

    def test_blocks_rm_rf_variants(self):
        cases = [
            "rm -rf /",
            "rm -fr ./build",
            "rm -r -f node_modules",
            "rm -f -r dist",
            "rm --recursive --force logs"
        ]
        for cmd in cases:
            blocked, reason = is_dangerous(cmd)
            self.assertTrue(blocked, f"Expected {cmd} to be blocked")
            self.assertIn("rm -rf", reason)

    def test_blocks_drop_table(self):
        blocked, reason = is_dangerous("psql -c 'DROP TABLE users;'")
        self.assertTrue(blocked)
        self.assertIn("DROP TABLE", reason)

    def test_blocks_truncate(self):
        blocked, reason = is_dangerous("mysql -e 'TRUNCATE TABLE accounts'")
        self.assertTrue(blocked)
        self.assertIn("TRUNCATE", reason)

    def test_blocks_forced_push(self):
        self.assertTrue(is_dangerous("git push origin main --force")[0])
        self.assertTrue(is_dangerous("git push -f origin feat")[0])

    def test_blocks_unconstrained_delete(self):
        blocked, reason = is_dangerous("sqlite3 app.db 'DELETE FROM sessions'")
        self.assertTrue(blocked)
        self.assertIn("DELETE without WHERE", reason)

    def test_allows_safe_commands(self):
        safe = [
            "git status",
            "git push origin main",
            "rm file.txt",
            "ls -la",
            "sqlite3 app.db 'DELETE FROM sessions WHERE id = 123'",
            "SELECT * FROM users"
        ]
        for cmd in safe:
            blocked, _ = is_dangerous(cmd)
            self.assertFalse(blocked, f"Should allow: {cmd}")

if __name__ == "__main__":
    unittest.main()
