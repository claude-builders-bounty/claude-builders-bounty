import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "destructive_command_guard.py"
spec = importlib.util.spec_from_file_location("guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DestructiveCommandGuardTests(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertEqual(guard.find_block_reason("rm -rf build"), "rm -rf")

    def test_blocks_drop_table(self):
        self.assertEqual(guard.find_block_reason("psql -c 'DROP TABLE users'"), "DROP TABLE")

    def test_blocks_force_push(self):
        self.assertEqual(guard.find_block_reason("git push origin main --force"), "git push --force")
        self.assertEqual(guard.find_block_reason("git push -f origin main"), "git push --force")

    def test_blocks_truncate(self):
        self.assertEqual(guard.find_block_reason("TRUNCATE audit_log"), "TRUNCATE")

    def test_blocks_delete_without_where(self):
        self.assertEqual(
            guard.find_block_reason("DELETE FROM sessions"),
            "DELETE FROM without WHERE",
        )

    def test_allows_delete_with_where(self):
        self.assertIsNone(guard.find_block_reason("DELETE FROM sessions WHERE id = 1"))

    def test_allows_normal_commands(self):
        self.assertIsNone(guard.find_block_reason("ls -la && git status"))


if __name__ == "__main__":
    unittest.main()
