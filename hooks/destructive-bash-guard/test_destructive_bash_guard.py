import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("destructive_bash_guard.py")
spec = importlib.util.spec_from_file_location("destructive_bash_guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


def payload(command: str) -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
    )


class DestructiveBashGuardTest(unittest.TestCase):
    def test_allows_normal_bash_command(self) -> None:
        self.assertIsNone(guard.find_block_reason("git status && ls -la"))

    def test_allows_delete_with_where_clause(self) -> None:
        self.assertIsNone(
            guard.find_block_reason("psql -c 'DELETE FROM sessions WHERE id = 1'")
        )

    def test_blocks_rm_rf_with_split_flags(self) -> None:
        reason = guard.find_block_reason("sudo rm -r -f ./dist")
        self.assertIsNotNone(reason)
        self.assertIn("rm -rf", reason)

    def test_blocks_force_push(self) -> None:
        reason = guard.find_block_reason("git push --force origin main")
        self.assertIsNotNone(reason)
        self.assertIn("overwrite", reason)

    def test_blocks_drop_table_case_insensitively(self) -> None:
        reason = guard.find_block_reason("psql -c 'drop table users;'")
        self.assertIsNotNone(reason)
        self.assertIn("DROP TABLE", reason)

    def test_blocks_truncate(self) -> None:
        reason = guard.find_block_reason("mysql -e 'TRUNCATE audit_events'")
        self.assertIsNotNone(reason)
        self.assertIn("TRUNCATE", reason)

    def test_blocks_delete_without_where(self) -> None:
        reason = guard.find_block_reason("psql -c 'DELETE FROM sessions;'")
        self.assertIsNotNone(reason)
        self.assertIn("DELETE FROM", reason)

    def test_main_denies_and_logs_blocked_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            stdin = io.StringIO(payload("rm -rf ./build"))
            stdout = io.StringIO()
            with patch.object(guard, "BLOCKED_LOG", log_path), patch(
                "sys.stdin", stdin
            ), redirect_stdout(stdout):
                exit_code = guard.main()

            self.assertEqual(exit_code, 0)
            decision = json.loads(stdout.getvalue())
            hook_output = decision["hookSpecificOutput"]
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("Blocked destructive Bash command", hook_output["permissionDecisionReason"])
            self.assertIn("rm -rf", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
