from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("block_destructive_commands.py")


class DestructiveCommandBlockerTests(unittest.TestCase):
    def run_hook(self, command: str, log_path: Path) -> subprocess.CompletedProcess[str]:
        payload = {
            "session_id": "test-session",
            "cwd": "/tmp/example-project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
        env = os.environ.copy()
        env["CLAUDE_BLOCKED_LOG"] = str(log_path)
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def assert_blocked(self, command: str, expected_reason: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            result = self.run_hook(command, log_path)

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn(expected_reason, hook_output["permissionDecisionReason"])

            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], command)
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")
            self.assertIn(expected_reason, log_entry["reason"])
            self.assertIn("timestamp", log_entry)

    def assert_allowed(self, command: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            result = self.run_hook(command, log_path)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse(log_path.exists())

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "rm with both recursive and force")
        self.assert_blocked("rm -rf /", "rm with both recursive and force")
        self.assert_blocked("rm -rf ./folder", "rm with both recursive and force")
        self.assert_blocked("sudo rm -Rf /tmp/example", "rm with both recursive and force")
        self.assert_blocked(
            "rm --recursive --force ./dist", "rm with both recursive and force"
        )

    def test_blocks_sql_destructive_patterns(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("sqlite3 app.db 'TRUNCATE TABLE users'", "TRUNCATE")
        self.assert_blocked("mysql -e 'DELETE FROM users'", "DELETE FROM without")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "force-pushing")
        self.assert_blocked("git -C repo push --force-with-lease", "force-pushing")

    def test_blocks_even_when_log_write_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir)
            result = self.run_hook("rm -rf /", log_path)

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("could not be written", hook_output["permissionDecisionReason"])

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("ls")
        self.assert_allowed("git status")
        self.assert_allowed("echo hello")
        self.assert_allowed("python script.py")
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm -r build")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 42'")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'")
        self.assert_allowed("echo 'rm -rf build'")


if __name__ == "__main__":
    unittest.main()
