#!/usr/bin/env python3
"""Tests for pre_tool_use_blocker.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("pre_tool_use_blocker.py")


class PreToolUseBlockerTests(unittest.TestCase):
    def run_hook(self, command: str, tool_name: str = "Bash") -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": tool_name,
                "cwd": "/tmp/example-project",
                "tool_input": {"command": command},
            }
            env = {**os.environ, "CLAUDE_HOOK_BLOCK_LOG": str(log_path)}
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            output = json.loads(result.stdout)
            if output:
                self.assertTrue(log_path.exists())
                log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
                self.assertEqual(log_entry["command"], command)
                self.assertEqual(log_entry["project_path"], "/tmp/example-project")
                self.assertIn("timestamp", log_entry)
            return output

    def assert_blocked(self, command: str, expected_text: str) -> None:
        output = self.run_hook(command)
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn(expected_text, output["systemMessage"])

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf ./dist", "rm -rf")
        self.assert_blocked("rm -fr ./dist", "rm -rf")

    def test_blocks_git_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('sqlite3 app.db "TRUNCATE TABLE users"', "TRUNCATE")
        self.assert_blocked('sqlite3 app.db "DELETE FROM users"', "DELETE FROM")

    def test_allows_delete_with_where(self) -> None:
        self.assertEqual(self.run_hook('sqlite3 app.db "DELETE FROM users WHERE id = 1"'), {})

    def test_allows_normal_bash(self) -> None:
        self.assertEqual(self.run_hook("git status --short"), {})
        self.assertEqual(self.run_hook("echo hello"), {})

    def test_ignores_non_bash_tools(self) -> None:
        self.assertEqual(self.run_hook("rm -rf ./dist", tool_name="Read"), {})


if __name__ == "__main__":
    unittest.main()
