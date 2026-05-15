#!/usr/bin/env python3
"""Self-contained tests for the destructive Bash blocker hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).parent / ".claude" / "hooks" / "block-destructive-bash.py"


def run_hook(command: str, home: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["HOME"] = home
    env["USERPROFILE"] = home
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class BlockDestructiveBashTest(unittest.TestCase):
    def test_safe_commands_do_not_emit_decision(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook("git status && ls -la", home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(home) / ".claude/hooks/blocked.log").exists())

    def test_blocks_destructive_patterns_and_logs_them(self) -> None:
        destructive_commands = [
            "rm -rf build",
            "rm -fr ./dist",
            "psql -c 'DROP TABLE users'",
            "psql -c 'TRUNCATE sessions'",
            "git push --force origin main",
            "psql -c 'DELETE FROM users'",
        ]
        with tempfile.TemporaryDirectory() as home:
            for command in destructive_commands:
                result = run_hook(command, home)
                self.assertEqual(result.returncode, 0)
                decision = json.loads(result.stdout)
                hook_output = decision["hookSpecificOutput"]
                self.assertEqual(hook_output["hookEventName"], "PreToolUse")
                self.assertEqual(hook_output["permissionDecision"], "deny")
                self.assertIn("Blocked potentially destructive Bash command", hook_output["permissionDecisionReason"])

            log_path = Path(home) / ".claude/hooks/blocked.log"
            log = log_path.read_text(encoding="utf-8")
            for command in destructive_commands:
                self.assertIn(command, log)
            self.assertIn("project=/tmp/example-project", log)

    def test_delete_from_with_where_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook("psql -c 'DELETE FROM users WHERE id = 1'", home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
