import unittest
import tempfile
from pathlib import Path
from pre_tool_use_hook import is_command_dangerous, inspect_command, log_blocked

class TestPreToolUseHook(unittest.TestCase):
    def test_blocks_rm_rf(self):
        dangerous, _ = is_command_dangerous("rm -rf /")
        self.assertTrue(dangerous)

    def test_blocks_drop_table(self):
        dangerous, _ = is_command_dangerous("DROP TABLE users;")
        self.assertTrue(dangerous)

    def test_blocks_git_force_push(self):
        dangerous, _ = is_command_dangerous("git push origin main --force")
        self.assertTrue(dangerous)

    def test_blocks_delete_without_where(self):
        dangerous, _ = is_command_dangerous("DELETE FROM accounts;")
        self.assertTrue(dangerous)

    def test_allows_delete_with_where(self):
        dangerous, _ = is_command_dangerous("DELETE FROM accounts WHERE id = 123;")
        self.assertFalse(dangerous)

    def test_allows_safe_commands(self):
        safe_commands = ["git status", "ls -la", "pytest", "npm run build"]
        for cmd in safe_commands:
            dangerous, _ = is_command_dangerous(cmd)
            self.assertFalse(dangerous, f"Falsely blocked safe command: {cmd}")

    def test_logging_blocked_attempt(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            log_path = Path(tmp.name)
        try:
            log_blocked("rm -rf /tmp/test", "/my/project", log_file=log_path)
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("rm -rf", content)
            self.assertIn("/my/project", content)
        finally:
            log_path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
