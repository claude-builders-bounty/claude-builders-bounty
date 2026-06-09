#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "destructive_command_guard.py"


def run_hook(command, cwd):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
    }
    env = os.environ.copy()
    env["HOME"] = str(cwd)
    return subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def decision(stdout):
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["permissionDecision"]


def reason(stdout):
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["permissionDecisionReason"]


class GuardTests(unittest.TestCase):
    def test_blocks_rm_rf_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("rm -rf build", Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(decision(result.stdout), "deny")
            self.assertIn("rm -rf", reason(result.stdout))
            log = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            self.assertIn("rm -rf build", log.read_text())

    def test_blocks_delete_without_where_but_allows_delete_with_where(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocked = run_hook("psql -c 'DELETE FROM users'", Path(tmp))
            allowed = run_hook("psql -c 'DELETE FROM users WHERE id = 1'", Path(tmp))
            self.assertEqual(decision(blocked.stdout), "deny")
            self.assertIn("DELETE FROM without WHERE", reason(blocked.stdout))
            self.assertEqual(decision(allowed.stdout), "allow")

    def test_blocks_required_sql_and_git_patterns(self):
        cases = [
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("sqlite3 app.db 'TRUNCATE TABLE events'", "TRUNCATE"),
            ("git push --force origin main", "git push --force"),
            ("git push -f origin main", "git push --force"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for command, expected_reason in cases:
                with self.subTest(command=command):
                    result = run_hook(command, Path(tmp))
                    self.assertEqual(decision(result.stdout), "deny")
                    self.assertIn(expected_reason, reason(result.stdout))

    def test_allows_force_with_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("git push --force-with-lease origin main", Path(tmp))
            self.assertEqual(decision(result.stdout), "allow")

    def test_allows_non_bash_tool_and_normal_bash_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            normal = run_hook("ls -la && git status", Path(tmp))
            self.assertEqual(decision(normal.stdout), "allow")

            payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
            env = os.environ.copy()
            env["HOME"] = tmp
            non_bash = subprocess.run(
                ["python3", str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(decision(non_bash.stdout), "allow")


if __name__ == "__main__":
    unittest.main()
