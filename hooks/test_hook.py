import unittest
from pre_tool_use_hook import check_command

class TestSecurityHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked, _ = check_command("rm -rf /")
        self.assertTrue(blocked)

        blocked, _ = check_command("rm -rf ./node_modules")
        self.assertTrue(blocked)

        blocked, _ = check_command("rm -fr dist")
        self.assertTrue(blocked)

    def test_blocks_sql_destructions(self):
        blocked, _ = check_command("DROP TABLE users;")
        self.assertTrue(blocked)

        blocked, _ = check_command("TRUNCATE TABLE logs;")
        self.assertTrue(blocked)

        blocked, _ = check_command("DELETE FROM customers")
        self.assertTrue(blocked)

    def test_blocks_git_force(self):
        blocked, _ = check_command("git push origin main --force")
        self.assertTrue(blocked)

        blocked, _ = check_command("git push -f origin main")
        self.assertTrue(blocked)

    def test_allows_safe_commands(self):
        blocked, _ = check_command("git status")
        self.assertFalse(blocked)

        blocked, _ = check_command("npm run build")
        self.assertFalse(blocked)

        blocked, _ = check_command("rm single_file.txt")
        self.assertFalse(blocked)

        blocked, _ = check_command("DELETE FROM accounts WHERE id = 123;")
        self.assertFalse(blocked)

if __name__ == "__main__":
    unittest.main()
