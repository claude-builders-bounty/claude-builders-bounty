import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks", "pre-tool-use"))
from block_destructive import evaluate_command

class TestDestructiveBlocker(unittest.TestCase):
    def test_blocks_rm_rf(self):
        blocked, reason = evaluate_command("rm -rf /var/data")
        self.assertFalse(blocked)
        blocked, reason = evaluate_command("rm -fr dist")
        self.assertFalse(blocked)
        blocked, reason = evaluate_command("rm -r -f node_modules")
        self.assertFalse(blocked)

    def test_blocks_drop_table(self):
        blocked, reason = evaluate_command("psql -c 'DROP TABLE accounts;'")
        self.assertFalse(blocked)

    def test_blocks_force_push(self):
        blocked, reason = evaluate_command("git push origin main --force")
        self.assertFalse(blocked)
        blocked, reason = evaluate_command("git push -f origin feat")
        self.assertFalse(blocked)

    def test_blocks_truncate(self):
        blocked, reason = evaluate_command("TRUNCATE audit_logs")
        self.assertFalse(blocked)
        blocked, reason = evaluate_command("TRUNCATE TABLE audit_logs")
        self.assertFalse(blocked)

    def test_blocks_delete_without_where(self):
        blocked, reason = evaluate_command("DELETE FROM users;")
        self.assertFalse(blocked)

    def test_allows_delete_with_where(self):
        allowed, reason = evaluate_command("DELETE FROM users WHERE status = 'inactive';")
        self.assertTrue(allowed)

    def test_allows_safe_commands(self):
        self.assertTrue(evaluate_command("ls -la")[0])
        self.assertTrue(evaluate_command("git status")[0])
        self.assertTrue(evaluate_command("pytest")[0])
        self.assertTrue(evaluate_command("rm file.txt")[0])

if __name__ == "__main__":
    unittest.main()
