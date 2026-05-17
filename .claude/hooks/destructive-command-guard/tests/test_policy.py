import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from guard.policy import find_block_reason


class PolicyTests(unittest.TestCase):
    def assert_blocked_by(self, command: str, rule_id: str):
        decision = find_block_reason(command)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.rule_id, rule_id)

    def assert_allowed(self, command: str):
        self.assertIsNone(find_block_reason(command))

    def test_blocks_recursive_force_rm_variants(self):
        self.assert_blocked_by("rm -rf dist", "rm_recursive_force")
        self.assert_blocked_by("rm -fr dist", "rm_recursive_force")
        self.assert_blocked_by("sudo rm -r -f ./cache", "rm_recursive_force")
        self.assert_blocked_by("/bin/rm --recursive --force ./tmp", "rm_recursive_force")

    def test_allows_non_recursive_or_non_force_rm(self):
        self.assert_allowed("rm package-lock.json")
        self.assert_allowed("rm -r ./dist")
        self.assert_allowed("rm -f ./dist/file.txt")

    def test_blocks_force_git_push(self):
        self.assert_blocked_by("git push --force origin main", "git_push_force")
        self.assert_blocked_by("git push -f", "git_push_force")
        self.assert_blocked_by("git push origin +main", "git_push_force")

    def test_allows_normal_git_push_and_force_with_lease(self):
        self.assert_allowed("git push origin main")
        self.assert_allowed("git push --force-with-lease origin main")

    def test_blocks_sql_drop_and_truncate(self):
        self.assert_blocked_by('psql -c "DROP TABLE users;"', "drop_table")
        self.assert_blocked_by('sqlite3 app.db "TRUNCATE TABLE events;"', "truncate_table")

    def test_blocks_delete_without_where(self):
        self.assert_blocked_by('sqlite3 app.db "DELETE FROM sessions;"', "delete_without_where")
        self.assert_allowed('sqlite3 app.db "DELETE FROM sessions WHERE expires_at < now();"')

    def test_allows_normal_commands(self):
        self.assert_allowed("npm test")
        self.assert_allowed("git status --short")
        self.assert_allowed("echo 'DROP the table in the docs later'")


if __name__ == "__main__":
    unittest.main()

