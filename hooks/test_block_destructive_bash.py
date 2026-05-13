#!/usr/bin/env python3
"""Unit tests for block_destructive_bash.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("block_destructive_bash.py")


def run_hook(command: str, *, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }
    tmp_home = tempfile.TemporaryDirectory()
    env = os.environ.copy()
    env["HOME"] = tmp_home.name
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    result.tmp_home = tmp_home  # type: ignore[attr-defined]
    return result


class BlockDestructiveBashTest(unittest.TestCase):
    def assert_denied(self, command: str, expected: str) -> None:
        result = run_hook(command)
        self.addCleanup(result.tmp_home.cleanup)  # type: ignore[attr-defined]
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected, output["permissionDecisionReason"])

        log_path = Path(result.tmp_home.name) / ".claude" / "hooks" / "blocked.log"  # type: ignore[attr-defined]
        self.assertTrue(log_path.exists())
        log_entry = json.loads(log_path.read_text().strip())
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/example-project")

    def assert_allowed(self, command: str, *, tool_name: str = "Bash") -> None:
        result = run_hook(command, tool_name=tool_name)
        self.addCleanup(result.tmp_home.cleanup)  # type: ignore[attr-defined]
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        log_path = Path(result.tmp_home.name) / ".claude" / "hooks" / "blocked.log"  # type: ignore[attr-defined]
        self.assertFalse(log_path.exists())

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_denied("rm -rf build", "rm -rf")
        self.assert_denied("rm -fr /tmp/cache", "rm -rf")

    def test_blocks_sql_destructive_operations(self) -> None:
        self.assert_denied("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_denied("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_denied("sqlite3 app.db 'DELETE FROM users;'", "DELETE FROM")

    def test_blocks_force_push(self) -> None:
        self.assert_denied("git push --force origin main", "force push")
        self.assert_denied("git push -f origin main", "force push")

    def test_allows_normal_bash_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("rm build.log")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1;'" )
        self.assert_allowed("git push origin main")

    def test_ignores_non_bash_tools(self) -> None:
        self.assert_allowed("rm -rf build", tool_name="Read")


if __name__ == "__main__":
    unittest.main()
