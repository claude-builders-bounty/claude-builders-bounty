import importlib.util
import pathlib
import sys
import unittest


HOOK_PATH = pathlib.Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_commands.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_commands", HOOK_PATH)
hook = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hook
SPEC.loader.exec_module(hook)


class BlockDestructiveCommandsTest(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked = [
            "rm -rf /tmp/example",
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE audit_log",
            "DELETE FROM sessions",
        ]

        for command in blocked:
            self.assertIsNotNone(hook.block_reason(command), command)

    def test_allows_safe_commands(self):
        allowed = [
            "ls -la",
            "git push origin main",
            "DELETE FROM sessions WHERE expires_at < now()",
            "rm -r build",
            "python -m pytest",
        ]

        for command in allowed:
            self.assertIsNone(hook.block_reason(command), command)

    def test_delete_without_where_is_statement_scoped(self):
        self.assertIsNone(hook.block_reason("DELETE FROM sessions WHERE id = 1; SELECT 1"))
        self.assertIsNotNone(hook.block_reason("SELECT 1; DELETE FROM sessions"))


if __name__ == "__main__":
    unittest.main()
