#!/usr/bin/env python3
"""Unit tests for block_destructive_bash.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import block_destructive_bash as guard


class DetectionTests(unittest.TestCase):
    def assert_blocks(self, command: str, expected_reason: str) -> None:
        reasons = guard.detect_block_reasons(command)
        self.assertTrue(
            any(expected_reason in reason for reason in reasons),
            f"Expected {command!r} to block for {expected_reason!r}; got {reasons!r}",
        )

    def assert_allows(self, command: str) -> None:
        self.assertEqual(guard.detect_block_reasons(command), [])

    def test_blocks_recursive_forced_rm_variants(self) -> None:
        self.assert_blocks("rm -rf build", "recursive forced deletion")
        self.assert_blocks("sudo rm -fr /tmp/example", "recursive forced deletion")
        self.assert_blocks("rm -r -f node_modules", "recursive forced deletion")
        self.assert_blocks("FOO=1 command rm -rf build", "recursive forced deletion")

    def test_blocks_sql_destructive_statements(self) -> None:
        self.assert_blocks('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocks('sqlite3 app.db "TRUNCATE TABLE sessions"', "TRUNCATE")
        self.assert_blocks('mysql -e "DELETE FROM users"', "DELETE FROM without WHERE")

    def test_blocks_forced_git_push(self) -> None:
        self.assert_blocks("git push --force origin main", "forced git push")
        self.assert_blocks("GIT_SSH_COMMAND=ssh git push -f origin main", "forced git push")

    def test_allows_normal_commands(self) -> None:
        self.assert_allows("rm -r build")
        self.assert_allows("rm -f debug.log")
        self.assert_allows("git push origin main")
        self.assert_allows('psql -c "DELETE FROM users WHERE id = 1"')
        self.assert_allows("python -m pytest")


class HookContractTests(unittest.TestCase):
    def test_pre_tool_use_denies_and_logs(self) -> None:
        hook_path = Path(__file__).with_name("block_destructive_bash.py")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": "rm -rf build"},
        }

        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("recursive forced deletion", hook_output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["project_path"], "/tmp/project")
            self.assertEqual(log_entry["command"], "rm -rf build")


if __name__ == "__main__":
    unittest.main()
