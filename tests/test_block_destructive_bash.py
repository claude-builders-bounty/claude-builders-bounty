import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


HOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "hooks"
    / "block-destructive-bash"
    / "block_destructive_bash.py"
)

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def bash_event(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/project",
    }


class BlockDestructiveBashTests(unittest.TestCase):
    def test_allows_normal_bash_command(self):
        self.assertIsNone(hook.find_block_reason("npm test && git status"))

    def test_ignores_non_bash_tools(self):
        self.assertEqual(hook.command_from_event({"tool_name": "Read", "tool_input": {}}), "")

    def test_blocks_required_patterns(self):
        cases = [
            ("rm -rf build", "rm -rf"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push --force origin main", "git push --force"),
            ("psql -c 'TRUNCATE audit_logs'", "TRUNCATE"),
            ("psql -c 'DELETE FROM users;'", "DELETE FROM without WHERE"),
        ]

        for command, expected_rule in cases:
            with self.subTest(command=command):
                actual = hook.find_block_reason(command)
                self.assertIsNotNone(actual)
                self.assertEqual(actual[0], expected_rule)

    def test_allows_delete_from_with_where_clause(self):
        self.assertIsNone(hook.find_block_reason("psql -c 'DELETE FROM users WHERE id = 1;'"))

    def test_main_logs_and_returns_pretooluse_deny_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            stdin = json.dumps(bash_event("rm -rf build"))
            stdout = io.StringIO()

            with patch.object(hook, "LOG_PATH", log_path), patch.object(hook.sys, "stdin", io.StringIO(stdin)):
                with redirect_stdout(stdout):
                    self.assertEqual(hook.main(), 0)

            output = json.loads(stdout.getvalue())
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_record = json.loads(log_path.read_text().strip())
            self.assertEqual(log_record["command"], "rm -rf build")
            self.assertEqual(log_record["project_path"], "/tmp/project")


if __name__ == "__main__":
    unittest.main()
