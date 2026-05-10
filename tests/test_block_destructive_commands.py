import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hooks import block_destructive_commands as hook


class BlockDestructiveCommandsTests(unittest.TestCase):
    def test_allows_safe_bash_commands(self):
        event = self._event("ls -la && git status")

        self.assertIsNone(hook.handle_event(event))

    def test_ignores_non_bash_tools(self):
        event = self._event("rm -rf build")
        event["tool_name"] = "Read"

        self.assertIsNone(hook.handle_event(event))

    def test_blocks_recursive_force_rm(self):
        response = self._handle("rm -rf /tmp/demo")

        self.assertDenied(response, "rm -rf")

    def test_blocks_recursive_force_rm_with_split_flags(self):
        response = self._handle("sudo rm -r -f /tmp/demo")

        self.assertDenied(response, "rm -rf")

    def test_blocks_drop_table(self):
        response = self._handle('psql -c "DROP TABLE users"')

        self.assertDenied(response, "DROP TABLE")

    def test_blocks_git_force_push(self):
        response = self._handle("git push origin main --force-with-lease")

        self.assertDenied(response, "git push --force")

    def test_blocks_truncate(self):
        response = self._handle('mysql -e "TRUNCATE TABLE sessions"')

        self.assertDenied(response, "TRUNCATE")

    def test_blocks_delete_from_without_where(self):
        response = self._handle('psql -c "DELETE FROM users"')

        self.assertDenied(response, "DELETE FROM without WHERE")

    def test_allows_delete_from_with_where(self):
        event = self._event('psql -c "DELETE FROM users WHERE id = 1"')

        self.assertIsNone(hook.handle_event(event))

    def test_logs_blocked_attempts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            with patch.object(hook, "LOG_PATH", log_path):
                response = hook.handle_event(self._event("rm -rf build"))

            self.assertDenied(response, "rm -rf")
            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["cwd"], "/workspace/project")
            self.assertEqual(entry["reason"], "rm -rf")
            self.assertEqual(entry["command"], "rm -rf build")
            self.assertIn("timestamp", entry)

    def test_denies_command_when_log_file_cannot_be_written(self):
        with patch.object(hook, "_log_blocked_attempt", side_effect=OSError("read-only")):
            response = hook.handle_event(self._event("rm -rf build"))

        self.assertDenied(response, "rm -rf")
        self.assertIn("Log write failed", response["hookSpecificOutput"]["permissionDecisionReason"])

    def assertDenied(self, response, expected_reason):
        self.assertIsNotNone(response)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_reason, output["permissionDecisionReason"])

    def _handle(self, command):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(hook, "LOG_PATH", Path(tmpdir) / "blocked.log"):
                return hook.handle_event(self._event(command))

    def _event(self, command):
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/workspace/project",
            "tool_input": {
                "command": command
            },
        }


if __name__ == "__main__":
    unittest.main()
