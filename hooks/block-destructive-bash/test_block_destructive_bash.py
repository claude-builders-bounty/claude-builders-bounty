import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import block_destructive_bash as hook


class DetectBlockReasonTests(unittest.TestCase):
    def assert_blocked(self, command: str) -> None:
        self.assertIsNotNone(hook.detect_block_reason(command), command)

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(hook.detect_block_reason(command), command)

    def test_blocks_recursive_forced_rm_variants(self) -> None:
        self.assert_blocked("rm -rf /tmp/build")
        self.assert_blocked("rm -fr /tmp/build")
        self.assert_blocked("rm -r -f /tmp/build")
        self.assert_blocked("sudo rm --recursive --force /tmp/build")
        self.assert_blocked("bash -c 'rm -rf /tmp/build'")

    def test_allows_non_forced_rm_and_echo_text(self) -> None:
        self.assert_allowed("rm -r /tmp/build")
        self.assert_allowed("rm package-lock.json")
        self.assert_allowed("echo rm -rf /tmp/build")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main")
        self.assert_blocked("git push origin main -f")
        self.assert_blocked("git push --force-with-lease")

    def test_allows_normal_git_push(self) -> None:
        self.assert_allowed("git push origin main")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"')
        self.assert_blocked('psql -c "TRUNCATE TABLE users"')
        self.assert_blocked('psql -c "DELETE FROM users"')

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')


class HandleEventTests(unittest.TestCase):
    def test_denies_and_logs_blocked_bash_command(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": "rm -rf /tmp/build"},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"CLAUDE_HOOKS_DIR": temp_dir}):
                output = hook.handle_event(payload)

            self.assertIsNotNone(output)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_path = os.path.join(temp_dir, "blocked.log")
            with open(log_path, "r", encoding="utf-8") as handle:
                log_entry = json.loads(handle.readline())
            self.assertEqual(log_entry["attempted_command"], "rm -rf /tmp/build")
            self.assertEqual(log_entry["project_path"], "/tmp/project")
            self.assertIn("timestamp", log_entry)

    def test_ignores_non_bash_tool(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "cwd": "/tmp/project",
            "tool_input": {"file_path": "/tmp/file"},
        }
        self.assertIsNone(hook.handle_event(payload))

    def test_main_emits_no_output_for_allowed_command(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": "npm test"},
        }

        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with patch.object(hook.sys, "stdin", stdin):
            with redirect_stdout(stdout):
                self.assertEqual(hook.main(), 0)

        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
