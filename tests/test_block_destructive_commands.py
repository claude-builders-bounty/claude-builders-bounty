#!/usr/bin/env python3
"""Regression tests for block_destructive_commands.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_commands.py"


class DestructiveCommandHookTest(unittest.TestCase):
    def tearDown(self) -> None:
        if hasattr(self, "temp_home"):
            self.temp_home.cleanup()

    def run_hook(self, command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        self.temp_home = tempfile.TemporaryDirectory()
        env = os.environ.copy()
        env["HOME"] = self.temp_home.name
        env["USERPROFILE"] = self.temp_home.name
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def assert_blocked(self, command: str, reason: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(reason, result.stderr)
        log_path = Path(self.temp_home.name) / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_path.exists())
        log_entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(log_entry["reason"], reason)
        self.assertEqual(log_entry["command"], command)

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf dist", "rm -rf")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked("mysql -e 'TRUNCATE audit_log'", "TRUNCATE")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_blocked("sqlite3 app.db 'DELETE FROM sessions;'", "DELETE FROM without WHERE")

    def test_allows_delete_with_where(self) -> None:
        result = self.run_hook("sqlite3 app.db 'DELETE FROM sessions WHERE id = 1;'")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ignores_non_bash_tools(self) -> None:
        result = self.run_hook("rm -rf dist", tool_name="Read")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
