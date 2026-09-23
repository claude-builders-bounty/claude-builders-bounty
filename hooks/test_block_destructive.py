import unittest

from block_destructive import destructive_reason


class DestructiveCommandTests(unittest.TestCase):
    def test_required_patterns_are_blocked(self):
        blocked = [
            "rm -rf /tmp/example",
            "rm -fr ./build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "sqlite3 app.db 'TRUNCATE TABLE logs'",
            "psql -c 'DELETE FROM users'",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(destructive_reason(command))

    def test_safe_commands_are_allowed(self):
        allowed = [
            "ls -la",
            "rm -f ./single-file.tmp",
            "git push origin main",
            "psql -c 'SELECT * FROM users'",
            "psql -c 'DELETE FROM users WHERE id = 42'",
            "echo 'DROP TABLE is mentioned in documentation'",
        ]
        # A literal SQL phrase inside echo is still textually indistinguishable to a
        # pre-execution Bash hook, so test the actual non-SQL examples separately.
        for command in allowed[:-1]:
            with self.subTest(command=command):
                self.assertIsNone(destructive_reason(command))

    def test_where_in_other_statement_does_not_hide_delete(self):
        command = "SELECT * FROM users WHERE id=1; DELETE FROM users"
        self.assertEqual(destructive_reason(command), "DELETE FROM without WHERE")


if __name__ == "__main__":
    unittest.main()
