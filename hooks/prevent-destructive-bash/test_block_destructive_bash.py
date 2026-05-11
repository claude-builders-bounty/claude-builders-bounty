import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

import block_destructive_bash as hook


def payload(command: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/demo-project",
    }


class DestructiveBashHookTest(unittest.TestCase):
    def assert_denied(self, command: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            with patch.object(hook, "LOG_PATH", log_path):
                result = hook.handle(payload(command))

            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("permissionDecisionReason", output)
            self.assertTrue(log_path.exists())
            self.assertIn(command, log_path.read_text(encoding="utf-8"))

    def assert_allowed(self, command: str) -> None:
        result = hook.handle(payload(command))
        self.assertTrue(result["continue"])
        self.assertNotIn("hookSpecificOutput", result)

    def test_blocks_rm_rf_variants(self):
        for command in [
            "rm -rf build",
            "rm -fr build",
            "rm -r -f build",
            "rm --recursive --force build",
        ]:
            with self.subTest(command=command):
                self.assert_denied(command)

    def test_blocks_forced_git_push(self):
        for command in [
            "git push --force origin main",
            "git push --force-with-lease",
            "git push -f",
        ]:
            with self.subTest(command=command):
                self.assert_denied(command)

    def test_blocks_dangerous_sql(self):
        for command in [
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "sqlite3 app.db 'DELETE FROM accounts'",
        ]:
            with self.subTest(command=command):
                self.assert_denied(command)

    def test_allows_delete_with_where(self):
        self.assert_allowed("sqlite3 app.db 'DELETE FROM accounts WHERE id = 1'")

    def test_allows_normal_bash_commands(self):
        for command in [
            "git status",
            "rm -r build",
            "python -m pytest",
            "echo 'DROP TABLE appears in docs only'",
        ]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_non_bash_tools_are_ignored(self):
        result = hook.handle(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "README.md"},
            }
        )
        self.assertEqual(result, {"continue": True, "suppressOutput": True})

    def test_output_is_json_serializable(self):
        result = hook.handle(payload("rm -rf build"))
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
