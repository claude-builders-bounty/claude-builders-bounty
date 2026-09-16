import unittest

from block_destructive import reason_for


class GuardTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        for command in (
            "rm -rf build",
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE TABLE audit_log",
            "DELETE FROM payments",
        ):
            self.assertIsNotNone(reason_for(command), command)

    def test_allows_scoped_or_normal_commands(self):
        for command in (
            "rm -r build",
            "git push origin feature/guard",
            "DELETE FROM payments WHERE id = 7",
            "npm test",
        ):
            self.assertIsNone(reason_for(command), command)


if __name__ == "__main__":
    unittest.main()
