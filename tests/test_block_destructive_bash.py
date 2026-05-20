import unittest

from hooks.block_destructive_bash import blocked_reason, extract_command


class BlockDestructiveBashTest(unittest.TestCase):
    def assert_blocked(self, command: str) -> None:
        self.assertIsNotNone(blocked_reason(command))

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(blocked_reason(command))

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf build")
        self.assert_blocked("rm -fr ./tmp")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'")
        self.assert_blocked("mysql -e 'TRUNCATE sessions'")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM users'")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main")
        self.assert_blocked("git push origin main --force-with-lease --force")

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("git push origin feature-branch")
        self.assert_allowed("rm -r build")
        self.assert_allowed("python -m pytest")

    def test_extracts_claude_hook_command(self) -> None:
        payload = {"tool_name": "Bash", "tool_input": {"command": "npm test"}}
        self.assertEqual(extract_command(payload), "npm test")


if __name__ == "__main__":
    unittest.main()
