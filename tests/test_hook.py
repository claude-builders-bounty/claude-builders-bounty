import unittest
from pre_tool_use import evaluate_command

class TestPreToolUseHook(unittest.TestCase):
    def test_blocks_dangerous(self):
        self.assertFalse(evaluate_command("rm -rf /", "/tmp"))
        self.assertFalse(evaluate_command("DROP TABLE users", "/tmp"))
        self.assertFalse(evaluate_command("DELETE FROM accounts", "/tmp"))
        self.assertFalse(evaluate_command("git push origin main --force", "/tmp"))

    def test_allows_safe(self):
        self.assertTrue(evaluate_command("ls -la", "/tmp"))
        self.assertTrue(evaluate_command("git push origin feature-branch", "/tmp"))
        self.assertTrue(evaluate_command("DELETE FROM users WHERE id=1", "/tmp"))
        self.assertTrue(evaluate_command("rm -rf node_modules", "/tmp"))

if __name__ == "__main__":
    unittest.main()

