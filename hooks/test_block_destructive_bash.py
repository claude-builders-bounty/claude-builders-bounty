#!/usr/bin/env python3
"""Dependency-free tests for the Claude Code destructive-command hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).with_name("block-destructive-bash.py")


def run_hook(command: str, *, cwd: str = "/tmp/example", tool_name: str = "Bash", home: str) -> subprocess.CompletedProcess[str]:
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": cwd,
    }
    environment = dict(os.environ)
    environment["HOME"] = home
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )


class DestructiveHookTests(unittest.TestCase):
    def test_blocks_destructive_commands_and_logs_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            blocked = [
                "rm -rf build",
                "rm -fr build",
                "rm -r -f build",
                "env FOO=bar rm -rf build",
                "sudo /bin/rm -r -f build",
                "git push --force origin main",
                "git push -f origin main",
                "git -C repo push --force-with-lease origin main",
                "DROP TABLE users",
                "TRUNCATE TABLE users",
                "DELETE FROM users",
                "echo ready && rm -rf build",
            ]
            for command in blocked:
                with self.subTest(command=command):
                    result = run_hook(command, home=home)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stderr, "")
                    decision = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(decision["permissionDecision"], "deny")
                    self.assertIn("Blocked by destructive-command guard", decision["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), len(blocked))
            self.assertTrue(all('cwd="/tmp/example"' in line for line in lines))

    def test_allows_safe_commands_and_scoped_delete(self) -> None:
        safe = [
            "npm test",
            "rm -f one-file.log",
            "env FOO=bar rm -f one-file.log",
            "sudo /bin/rm -f one-file.log",
            "git push origin main",
            "DELETE FROM users WHERE id = 1",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "echo 'DROP TABLE users'",
            "printf 'TRUNCATE TABLE users'",
        ]
        with tempfile.TemporaryDirectory() as home:
            for command in safe:
                with self.subTest(command=command):
                    result = run_hook(command, home=home)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(result.stderr, "")
            self.assertFalse((Path(home) / ".claude" / "hooks" / "blocked.log").exists())

    def test_ignores_non_bash_events_and_bad_json(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook("rm -rf build", tool_name="Read", home=home)
            self.assertEqual(result.stdout, "")
            malformed = subprocess.run(
                [sys.executable, str(HOOK)],
                input="not-json",
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": home},
                check=False,
            )
            self.assertEqual(malformed.returncode, 0)
            self.assertEqual(malformed.stdout, "")


if __name__ == "__main__":
    unittest.main()
