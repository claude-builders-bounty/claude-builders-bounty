from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("block_destructive_commands.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_commands", MODULE_PATH)
hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(hook)


def event(command: str) -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/project",
        }
    )


class DestructiveCommandGuardTests(unittest.TestCase):
    def run_hook(self, command: str, log_path: Path) -> str:
        previous_log_path = os.environ.get(hook.LOG_PATH_ENV)
        os.environ[hook.LOG_PATH_ENV] = str(log_path)
        stdout = io.StringIO()
        try:
            exit_code = hook.main(io.StringIO(event(command)), stdout)
        finally:
            if previous_log_path is None:
                os.environ.pop(hook.LOG_PATH_ENV, None)
            else:
                os.environ[hook.LOG_PATH_ENV] = previous_log_path
        self.assertEqual(exit_code, 0)
        return stdout.getvalue()

    def assert_blocked(self, command: str, expected_reason: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            output = self.run_hook(command, log_path)
            payload = json.loads(output)
            decision = payload["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn(expected_reason, decision["permissionDecisionReason"])

            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], command)
            self.assertEqual(log_entry["project_path"], "/tmp/project")
            self.assertIn(expected_reason, log_entry["reason"])

    def assert_allowed(self, command: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            output = self.run_hook(command, log_path)
            self.assertEqual(output, "")
            self.assertFalse(log_path.exists())

    def test_blocks_rm_recursive_force(self) -> None:
        self.assert_blocked("rm -fr /tmp/build", "rm recursive force command")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE statement")

    def test_blocks_git_push_force(self) -> None:
        self.assert_blocked("git push origin main --force", "git push --force")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked("psql -c 'TRUNCATE audit_log'", "TRUNCATE statement")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_blocked("mysql -e 'DELETE FROM sessions;'", "DELETE FROM without WHERE")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed("mysql -e 'DELETE FROM sessions WHERE expires_at < NOW();'")

    def test_allows_normal_command(self) -> None:
        self.assert_allowed("npm test")

    def test_ignores_non_bash_tool(self) -> None:
        stdout = io.StringIO()
        payload = json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"command": "rm -rf /tmp/build"},
            }
        )
        self.assertEqual(hook.main(io.StringIO(payload), stdout), 0)
        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
