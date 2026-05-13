#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("destructive_command_blocker.py")


class DestructiveCommandBlockerTest(unittest.TestCase):
    def run_hook(self, command: str, home: str | None = None) -> dict:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        env = os.environ.copy()
        if home:
            env["HOME"] = home
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        return json.loads(result.stdout)

    def assert_denied(self, command: str) -> None:
        output = self.run_hook(command)
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("Blocked destructive Bash command", output["permissionDecisionReason"])

    def test_blocks_rm_rf(self) -> None:
        self.assert_denied("rm -rf build/")
        self.assert_denied("rm -fr build/")
        self.assert_denied("sudo rm --recursive --force build/")
        self.assert_denied("env -i PATH=/usr/bin rm -rf build/")
        self.assert_denied("bash -c 'rm -rf build/'")

    def test_blocks_drop_table(self) -> None:
        self.assert_denied("psql -c 'DROP TABLE users;'")

    def test_blocks_force_push(self) -> None:
        self.assert_denied("git push --force origin main")
        self.assert_denied("git push -f origin main")
        self.assert_denied("git push origin +main")
        self.assert_denied("git -c push.default=simple push --force-with-lease origin main")
        self.assert_denied("git --git-dir .git push --force origin main")

    def test_ignores_non_bash_payloads_and_bad_json(self) -> None:
        payload = {"tool_name": "Read", "tool_input": {"file_path": "rm -rf notes.txt"}}
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout)["permissionDecision"], "allow")

        bad = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not json",
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(bad.stdout)["permissionDecision"], "allow")

    def test_blocks_truncate(self) -> None:
        self.assert_denied("mysql -e 'TRUNCATE audit_log;'")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_denied("psql -c 'DELETE FROM users;'")

    def test_allows_normal_commands(self) -> None:
        safe = [
            "ls -la",
            "git status --short",
            "python3 -m pytest",
            "psql -c 'DELETE FROM users WHERE id = 1;'",
            "grep -R 'rm -rf' README.md",
        ]
        for command in safe:
            with self.subTest(command=command):
                output = self.run_hook(command)
                self.assertEqual(output["permissionDecision"], "allow")

    def test_logs_blocked_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            output = self.run_hook("rm -rf /tmp/demo", home=home)
            self.assertEqual(output["permissionDecision"], "deny")
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            record = json.loads(log_path.read_text().strip())
            self.assertEqual(record["attempted_command"], "rm -rf /tmp/demo")
            self.assertEqual(record["project_path"], "/tmp/example-project")
            self.assertIn("timestamp", record)


if __name__ == "__main__":
    unittest.main()
