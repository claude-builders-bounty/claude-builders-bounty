import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"
spec = importlib.util.spec_from_file_location("block_destructive_bash", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class BlockDestructiveBashTests(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertIsNotNone(mod.block_reason("rm -rf dist"))

    def test_blocks_drop_table(self):
        self.assertIsNotNone(mod.block_reason("psql -c 'DROP TABLE users'"))

    def test_blocks_git_push_force(self):
        self.assertIsNotNone(mod.block_reason("git push origin main --force-with-lease"))

    def test_blocks_truncate(self):
        self.assertIsNotNone(mod.block_reason("TRUNCATE TABLE events"))

    def test_blocks_delete_without_where(self):
        self.assertIsNotNone(mod.block_reason("DELETE FROM users;"))

    def test_allows_delete_with_where(self):
        self.assertIsNone(mod.block_reason("DELETE FROM users WHERE id = 1;"))

    def test_allows_normal_commands(self):
        self.assertIsNone(mod.block_reason("git status && python -m unittest"))


if __name__ == "__main__":
    unittest.main()
