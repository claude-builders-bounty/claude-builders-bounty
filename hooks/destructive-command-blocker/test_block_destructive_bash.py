#!/usr/bin/env python3
"""Unit tests for the destructive Bash command blocker."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import block_destructive_bash as hook


HOOK_PATH = Path(__file__).with_name("block_destructive_bash.py")


class BlockedReasonTests(unittest.TestCase):
    def assert_blocked(self, command: str) -> None:
        self.assertIsNotNone(hook.blocked_reason(command), command)

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(hook.blocked_reason(command), command)

    def test_blocks_recursive_force_rm(self) -> None:
        self.assert_blocked("rm -rf build")
        self.assert_blocked("rm -fr ./tmp")
        self.assert_blocked("sudo rm -rf /var/tmp/app")

    def test_allows_scoped_rm(self) -> None:
        self.assert_allowed("rm build/output.txt")
        self.assert_allowed("rm -r build/cache")
        self.assert_allowed("rm -f build/output.txt")

    def test_blocks_sql_destruction(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'")
        self.assert_blocked("mysql -e 'TRUNCATE sessions'")
        self.assert_blocked("psql -c 'DELETE FROM users'")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed("psql -c 'DELETE FROM users WHERE id = 1'")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main")
        self.assert_blocked("git push -f origin main")
        self.assert_blocked("git push --force-with-lease origin main")

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin main")
        self.assert_allowed("grep -R 'DROP TABLE' docs/")


class HookIntegrationTests(unittest.TestCase):
    def run_hook(self, command: str) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": command},
        }
        return subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env={
                **os.environ,
                "CLAUDE_BLOCKED_LOG_PATH": str(Path(tempfile.gettempdir()) / "claude-blocked-test.log"),
            },
        )

    def test_safe_command_is_silent(self) -> None:
        result = self.run_hook("npm test")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocked_command_returns_pretool_deny(self) -> None:
        result = self.run_hook("git push --force origin main")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        output = data["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("Force-pushing", output["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
