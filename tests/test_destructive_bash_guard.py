from __future__ import annotations

import unittest

from hooks.destructive_bash_guard import validate_command


class DestructiveBashGuardTest(unittest.TestCase):
    def assert_blocked(self, command: str, rule: str) -> None:
        reasons = validate_command(command)
        self.assertTrue(any(reason.rule == rule for reason in reasons), reasons)

    def assert_allowed(self, command: str) -> None:
        self.assertEqual(validate_command(command), [])

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf dist", "rm -rf")
        self.assert_blocked("rm -fr dist", "rm -rf")
        self.assert_blocked("npm test && rm -rf /tmp/build", "rm -rf")

    def test_blocks_force_push_variants(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f", "git push --force")
        self.assert_blocked("git push --force-with-lease", "git push --force")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('psql -c "TRUNCATE users"', "TRUNCATE")
        self.assert_blocked('psql -c "DELETE FROM users"', "DELETE FROM without WHERE")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin feature")
        self.assert_allowed("rm dist/output.txt")
        self.assert_allowed("python3 scripts/build.py")


if __name__ == "__main__":
    unittest.main()
