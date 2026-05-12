from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block-destructive-bash.py"


class BlockDestructiveBashTests(unittest.TestCase):
    def run_hook(self, command: str, *, tool_name: str = "Bash") -> tuple[subprocess.CompletedProcess[str], Path]:
        home = Path(tempfile.mkdtemp())
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
            "hook_event_name": "PreToolUse",
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

    def assert_blocked(self, command: str, reason_fragment: str) -> None:
        result, log_path = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(reason_fragment, output["permissionDecisionReason"])

        self.assertTrue(log_path.exists())
        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(entry["attempted_command"], command)
        self.assertEqual(entry["project_path"], "/tmp/example-project")
        self.assertIn(reason_fragment, entry["reason"])
        self.assertIn("matched_rule", entry)
        self.assertIn("timestamp", entry)

    def assert_allowed(self, command: str, *, tool_name: str = "Bash") -> None:
        result, log_path = self.run_hook(command, tool_name=tool_name)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(log_path.exists())

    def test_blocks_rm_recursive_force_variants(self) -> None:
        self.assert_blocked("rm -rf build", "recursive and force")
        self.assert_blocked("sudo rm -r -f /tmp/demo", "recursive and force")
        self.assert_blocked("rm --recursive --force old-cache", "recursive and force")

    def test_blocks_git_force_push_variants(self) -> None:
        self.assert_blocked("git push --force origin main", "remote history")
        self.assert_blocked("git push -f", "remote history")
        self.assert_blocked("git push --force-with-lease", "remote history")

    def test_blocks_destructive_sql_in_sql_context(self) -> None:
        self.assert_blocked("sqlite3 app.db 'DROP TABLE users;'", "DROP TABLE")
        self.assert_blocked("psql -c 'truncate table events;'", "TRUNCATE")
        self.assert_blocked("mysql -e 'DELETE FROM sessions;'", "DELETE FROM without WHERE")

    def test_allows_safe_commands_and_passive_text(self) -> None:
        self.assert_allowed("ls -la")
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm file.txt")
        self.assert_allowed("rm -r old-folder")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < 123;'")
        self.assert_allowed("truncate -s 0 app.log")
        self.assert_allowed("echo 'DROP TABLE users;'")
        self.assert_allowed("grep 'DELETE FROM' migrations/*.sql")

    def test_ignores_non_bash_tools(self) -> None:
        self.assert_allowed("rm -rf build", tool_name="Read")

    def test_malformed_json_is_allowed_safely(self) -> None:
        home = Path(tempfile.mkdtemp())
        env = os.environ.copy()
        env["HOME"] = str(home)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="{not-json",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
