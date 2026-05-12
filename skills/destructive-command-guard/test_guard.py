#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import guard


class GuardDetectionTests(unittest.TestCase):
    def assert_blocked(self, command: str, contains: str) -> None:
        reason = guard.check_command(command)
        self.assertIsNotNone(reason, command)
        self.assertIn(contains, reason)

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(guard.check_command(command), command)

    def test_required_blocked_patterns(self) -> None:
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("rm -fr build", "rm -rf")
        self.assert_blocked("DROP TABLE users", "DROP")
        self.assert_blocked("drop database app", "DROP")
        self.assert_blocked("git push --force origin main", "git push")
        self.assert_blocked("git push -f origin main", "git push")
        self.assert_blocked("TRUNCATE TABLE sessions", "TRUNCATE")
        self.assert_blocked("DELETE FROM users;", "DELETE FROM")

    def test_common_wrappers_and_nested_shells(self) -> None:
        self.assert_blocked("sudo rm --recursive --force /tmp/app", "rm -rf")
        self.assert_blocked("bash -c 'rm -rf /tmp/app'", "rm -rf")
        self.assert_blocked("git push origin +main", "git push")
        self.assert_blocked("psql -c 'DELETE FROM audit_log;'", "DELETE FROM")

    def test_safe_commands_are_allowed(self) -> None:
        self.assert_allowed("rm file.txt")
        self.assert_allowed("rm -r build")
        self.assert_allowed("git push origin main")
        self.assert_allowed("DELETE FROM users WHERE id = 5;")
        self.assert_allowed("echo 'DROP TABLE users'")


class GuardHookProtocolTests(unittest.TestCase):
    def test_denies_and_logs_jsonl(self) -> None:
        payload = {"tool_input": {"command": "rm -rf /tmp/demo"}, "cwd": "/repo"}
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home}
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("guard.py"))],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            output = json.loads(proc.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(record["project_path"], "/repo")
            self.assertEqual(record["command"], "rm -rf /tmp/demo")

    def test_allows_safe_command_silently(self) -> None:
        payload = {"tool_input": {"command": "ls -la"}, "cwd": "/repo"}
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("guard.py"))],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
