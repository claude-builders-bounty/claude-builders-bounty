import importlib.util
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
assert SPEC and SPEC.loader
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


class DestructiveBashHookTests(unittest.TestCase):
    def assert_blocked(self, command: str) -> None:
        self.assertIsNotNone(hook.find_block_reason(command), command)

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(hook.find_block_reason(command), command)

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build")
        self.assert_blocked("rm -fr build")
        self.assert_blocked("sudo rm -rf /tmp/example")

    def test_blocks_sql_destructive_commands(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"')
        self.assert_blocked('mysql -e "TRUNCATE sessions"')
        self.assert_blocked('psql -c "DELETE FROM users"')

    def test_allows_delete_with_where_clause(self) -> None:
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')

    def test_blocks_git_push_force(self) -> None:
        self.assert_blocked("git push --force origin main")

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm -r dist")
        self.assert_allowed("grep -R 'DELETE FROM' docs/")

if __name__ == "__main__":
    unittest.main()
