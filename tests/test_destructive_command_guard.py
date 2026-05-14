from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive-command-guard" / "destructive_command_guard.py"


class DestructiveCommandGuardTests(unittest.TestCase):
    def run_hook(self, command: str, home: Path) -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/work/project",
        }
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def assert_denied(self, result: subprocess.CompletedProcess[str], expected_reason: str) -> None:
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_reason, output["permissionDecisionReason"])

    def test_safe_command_allows_without_log(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook("git status --short", Path(home))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(home) / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_recursive_force_and_logs_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            result = self.run_hook("rm -rf /tmp/build", home_path)

            self.assert_denied(result, "recursive and force")
            log_path = home_path / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["command"], "rm -rf /tmp/build")
            self.assertEqual(record["project_path"], "/work/project")

    def test_blocks_wrapped_rm_recursive_force(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook("sudo bash -c 'rm -fr ./dist'", Path(home))

            self.assert_denied(result, "recursive and force")

    def test_blocks_git_force_push(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook("git -C repo push --force-with-lease origin main", Path(home))

            self.assert_denied(result, "overwrite remote history")

    def test_blocks_sql_drop_table_through_database_client(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook('psql "$DATABASE_URL" -c "DROP TABLE users"', Path(home))

            self.assert_denied(result, "DROP TABLE")

    def test_blocks_delete_from_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook('mysql app -e "DELETE FROM users"', Path(home))

            self.assert_denied(result, "without a WHERE")

    def test_allows_delete_with_where_and_file_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            delete_result = self.run_hook(
                "sqlite3 app.db \"DELETE FROM sessions WHERE expires_at < datetime('now')\"",
                home_path,
            )
            truncate_result = self.run_hook("truncate -s 0 debug.log", home_path)

            self.assertEqual(delete_result.returncode, 0)
            self.assertEqual(delete_result.stdout, "")
            self.assertEqual(truncate_result.returncode, 0)
            self.assertEqual(truncate_result.stdout, "")
            self.assertFalse((home_path / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
