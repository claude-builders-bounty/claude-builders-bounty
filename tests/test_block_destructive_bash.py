from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block-destructive-bash.py"


class BlockDestructiveBashHookTest(unittest.TestCase):
    def run_hook(
        self,
        command: str,
        *,
        tool_name: str = "Bash",
        event_name: str = "PreToolUse",
    ) -> Tuple[subprocess.CompletedProcess, Path]:
        home = Path(tempfile.mkdtemp(prefix="claude-hook-test-"))
        payload = {
            "session_id": "test-session",
            "transcript_path": "/tmp/transcript.jsonl",
            "cwd": "/tmp/example-project",
            "hook_event_name": event_name,
            "tool_name": tool_name,
            "tool_input": {"command": command},
        }
        env = os.environ.copy()
        env["HOME"] = str(home)

        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        return result, home / ".claude" / "hooks" / "blocked.log"

    def assert_allowed(self, command: str) -> None:
        result, log_path = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(log_path.exists())

    def assert_blocked(self, command: str, expected_reason: str) -> None:
        result, log_path = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)

        output = json.loads(result.stdout)
        hook_output = output["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn(expected_reason, hook_output["permissionDecisionReason"])

        log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/example-project")
        self.assertIn(expected_reason, log_entry["reason"])
        self.assertIn("timestamp", log_entry)

    def test_allows_normal_bash_commands(self) -> None:
        self.assert_allowed("git status && python3 -m pytest")

    def test_ignores_non_bash_tools(self) -> None:
        result, log_path = self.run_hook("rm -rf build", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(log_path.exists())

    def test_blocks_rm_recursive_force(self) -> None:
        self.assert_blocked("rm -rf build", "rm with both recursive and force flags")
        self.assert_blocked("sudo rm -r -f /tmp/cache", "rm with both recursive and force flags")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git -C repo push -f origin main", "git push --force")
        self.assert_blocked("git push --force-with-lease origin main", "git push --force")

    def test_blocks_drop_table_and_sql_truncate(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users;'", "DROP TABLE")
        self.assert_blocked("psql -c 'TRUNCATE TABLE audit_log;'", "TRUNCATE")

    def test_allows_file_truncate_command(self) -> None:
        self.assert_allowed("truncate -s 0 app.log")

    def test_blocks_delete_from_without_where(self) -> None:
        self.assert_blocked("psql -c 'DELETE FROM sessions;'", "DELETE FROM without a WHERE")

    def test_allows_delete_from_with_where(self) -> None:
        self.assert_allowed("psql -c 'DELETE FROM sessions WHERE expires_at < now();'")


if __name__ == "__main__":
    unittest.main()
