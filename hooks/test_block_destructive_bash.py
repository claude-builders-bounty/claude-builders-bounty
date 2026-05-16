import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from block_destructive_bash import block_reason


class BlockDestructiveBashTest(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertIsNotNone(block_reason("rm -rf build"))

    def test_blocks_drop_table(self):
        self.assertIsNotNone(block_reason("psql -c 'DROP TABLE users'"))

    def test_blocks_git_push_force(self):
        self.assertIsNotNone(block_reason("git push origin main --force"))

    def test_blocks_truncate(self):
        self.assertIsNotNone(block_reason("TRUNCATE audit_log"))

    def test_blocks_delete_from_without_where(self):
        self.assertIsNotNone(block_reason("DELETE FROM users"))

    def test_allows_delete_from_with_where(self):
        self.assertIsNone(block_reason("DELETE FROM users WHERE id = 1"))

    def test_allows_normal_bash(self):
        self.assertIsNone(block_reason("python -m pytest"))


if __name__ == "__main__":
    unittest.main()
