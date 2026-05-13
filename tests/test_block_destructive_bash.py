from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, log_path: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = {**os.environ, "CLAUDE_BLOCKED_LOG": str(log_path)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashHookTest(unittest.TestCase):
    def test_allows_normal_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("git status && ls -la", Path(directory) / "blocked.log")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf /tmp/build", "rm -rf")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked('mysql -e "TRUNCATE users"', "TRUNCATE")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_blocked('psql -c "DELETE FROM users"', "DELETE FROM without a WHERE")

    def test_allows_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook('psql -c "DELETE FROM users WHERE id = 1"', Path(directory) / "blocked.log")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def assert_blocked(self, command: str, reason_fragment: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "blocked.log"
            result = run_hook(command, log_path)

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn(reason_fragment, hook_output["permissionDecisionReason"])

            log_record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_record["attempted_command"], command)
            self.assertEqual(log_record["project_path"], "/tmp/example-project")


if __name__ == "__main__":
    unittest.main()
