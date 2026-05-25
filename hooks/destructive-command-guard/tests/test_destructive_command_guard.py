from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "destructive_command_guard.py"


def run_hook(command: str, home: Path | None = None) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveCommandGuardTest(unittest.TestCase):
    def assert_blocked(self, command: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(command, Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")

            log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_record["attempted_command"], command)
            self.assertEqual(log_record["project_path"], "/tmp/example-project")
            self.assertIn("timestamp", log_record)
            return output

    def assert_allowed(self, command: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(command, Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertFalse(log_path.exists())

    def test_blocks_rm_rf_variants(self) -> None:
        for command in (
            "rm -rf build",
            "rm -fr build",
            "rm -r -f build",
            "rm --recursive --force build",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_blocks_sql_dangerous_statements(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'")
        self.assert_blocked("mysql -e 'TRUNCATE sessions'")
        self.assert_blocked("psql -c 'DELETE FROM accounts'")

    def test_allows_delete_from_with_where(self) -> None:
        self.assert_allowed("psql -c 'DELETE FROM accounts WHERE id = 1'")

    def test_blocks_forced_git_push(self) -> None:
        for command in (
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "git push origin +main",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_allows_normal_commands(self) -> None:
        for command in (
            "npm test",
            "git push origin main",
            "rm -r build",
            "rm --recursive build",
            "rm --force old.log",
            "echo 'DELETE FROM accounts WHERE id = 1'",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_ignores_non_bash_tool_calls(self) -> None:
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
