#!/usr/bin/env python3
"""Unit tests for the destructive Bash Claude Code hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name("block_destructive_bash.py")


class DestructiveHookTests(unittest.TestCase):
    def run_hook(self, command: str, *, home: Path | None = None) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
        env = os.environ.copy()
        if home is not None:
            env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def assert_blocked(self, command: str, pattern: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_hook(command, home=home)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn(pattern, decision["permissionDecisionReason"])

            log_path = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["command"], command)
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")
            self.assertEqual(log_entry["pattern"], pattern)
            self.assertIn("timestamp", log_entry)

    def test_all_required_patterns_block(self) -> None:
        cases = [
            ("rm -rf build", "rm -rf"),
            ("sqlite3 app.db 'DROP TABLE users'", "DROP TABLE"),
            ("git push --force origin main", "git push --force"),
            ("psql -c 'TRUNCATE events'", "TRUNCATE"),
            ("sqlite3 app.db 'DELETE FROM sessions'", "DELETE FROM without WHERE"),
        ]
        for command, pattern in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, pattern)

    def test_delete_from_with_where_is_allowed(self) -> None:
        result = self.run_hook("sqlite3 app.db \"DELETE FROM sessions WHERE id = 1\"")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_normal_bash_is_allowed(self) -> None:
        result = self.run_hook("npm test")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_non_bash_event_is_allowed(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md"},
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
