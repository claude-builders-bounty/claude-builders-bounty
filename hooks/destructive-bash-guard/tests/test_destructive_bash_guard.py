import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "destructive_bash_guard.py"
)
spec = importlib.util.spec_from_file_location("destructive_bash_guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class DestructiveBashGuardTests(unittest.TestCase):
    def test_blocks_required_destructive_patterns(self):
        blocked = [
            "rm -rf /tmp/build",
            "DROP TABLE users",
            "TRUNCATE audit_log",
            "git push --force origin main",
            "git push -f origin main",
            "DELETE FROM users",
        ]

        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.block_reason(command))

    def test_allows_normal_commands_and_scoped_delete(self):
        allowed = [
            "ls -la",
            "git push origin main",
            "rm -r ./build",
            "DELETE FROM users WHERE id = 1",
            "python3 -m unittest",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.block_reason(command))

    def test_main_logs_and_denies_blocked_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_log = guard.BLOCKED_LOG
            guard.BLOCKED_LOG = Path(temp_dir) / "blocked.log"
            payload = {
                "tool_input": {"command": "DELETE FROM users"},
                "project_path": "/repo",
            }

            stdin = guard.sys.stdin
            guard.sys.stdin = io.StringIO(json.dumps(payload))
            output = io.StringIO()
            try:
                with redirect_stdout(output):
                    self.assertEqual(guard.main(), 0)
            finally:
                guard.sys.stdin = stdin
                guard.BLOCKED_LOG = original_log

            response = json.loads(output.getvalue())
            self.assertEqual(response["permissionDecision"], "deny")
            self.assertIn("DELETE FROM without WHERE", response["permissionDecisionReason"])

            log_text = (Path(temp_dir) / "blocked.log").read_text(encoding="utf-8")
            self.assertIn("/repo", log_text)
            self.assertIn("DELETE FROM users", log_text)


if __name__ == "__main__":
    unittest.main()
