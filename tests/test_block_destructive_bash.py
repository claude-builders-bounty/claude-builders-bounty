import unittest

from hooks.block_destructive_bash import get_block_reason


class DestructiveBashHookTests(unittest.TestCase):
    def assertBlocked(self, command: str) -> None:
        self.assertIsNotNone(get_block_reason(command))

    def assertAllowed(self, command: str) -> None:
        self.assertIsNone(get_block_reason(command))

    def test_blocks_rm_rf_variants(self) -> None:
        self.assertBlocked("rm -rf build")
        self.assertBlocked("rm -fr /tmp/example")
        self.assertBlocked("sudo rm -Rf ./dist")

    def test_blocks_sql_destructive_statements(self) -> None:
        self.assertBlocked("DROP TABLE users")
        self.assertBlocked("truncate table sessions")
        self.assertBlocked("DELETE FROM customers")

    def test_allows_delete_with_where_clause(self) -> None:
        self.assertAllowed("DELETE FROM customers WHERE id = 42")

    def test_blocks_force_push(self) -> None:
        self.assertBlocked("git push --force origin main")
        self.assertBlocked("git push -f")
        self.assertBlocked("git push --force-with-lease")

    def test_allows_normal_bash_commands(self) -> None:
        self.assertAllowed("ls -la")
        self.assertAllowed("git status --short")
        self.assertAllowed("rm file.txt")
        self.assertAllowed("python3 -m pytest")


if __name__ == "__main__":
    unittest.main()
