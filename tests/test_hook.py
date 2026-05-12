import unittest
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "hooks" / "block-destructive-bash" / "block_destructive_bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", MODULE_PATH)
hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(hook)

block_reason = hook.block_reason


class HookTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        self.assertIsNotNone(block_reason("rm -rf /tmp/example"))
        self.assertIsNotNone(block_reason("DROP TABLE users"))
        self.assertIsNotNone(block_reason("TRUNCATE audit_log"))
        self.assertIsNotNone(block_reason("git push origin main --force"))
        self.assertIsNotNone(block_reason("DELETE FROM users"))

    def test_allows_normal_commands(self):
        self.assertIsNone(block_reason("git status --short"))
        self.assertIsNone(block_reason("DELETE FROM users WHERE id = 1"))
        self.assertIsNone(block_reason("rm -r build-output"))


if __name__ == "__main__":
    unittest.main()
