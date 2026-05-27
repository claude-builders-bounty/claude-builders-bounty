#!/usr/bin/env python3
"""Unit tests for destructive_bash_guard.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive_bash_guard.py"


def run_hook(command: str, home: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "cwd": "/tmp/project",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["HOME"] = home
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashGuardTests(unittest.TestCase):
    def test_safe_command_passes_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook("git status && npm test", home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertFalse((Path(home) / ".claude/hooks/blocked.log").exists())

    def test_non_bash_tool_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook("rm -rf /tmp/example", home, tool_name="Read")
            self.assertEqual(result.returncode, 0)

    def test_blocks_rm_rf_and_logs_json(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook("rm -rf build", home)
            self.assertEqual(result.returncode, 2)
            self.assertIn("rm -rf", result.stderr)
            log_path = Path(home) / ".claude/hooks/blocked.log"
            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["command"], "rm -rf build")
            self.assertEqual(record["project_path"], "/tmp/project")
            self.assertIn("timestamp", record)

    def test_blocks_git_force_push(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(run_hook("git push --force origin main", home).returncode, 2)
            self.assertEqual(run_hook("git push -f origin main", home).returncode, 2)

    def test_blocks_drop_table_and_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(run_hook("psql -c 'DROP TABLE users'", home).returncode, 2)
            self.assertEqual(run_hook("mysql -e 'TRUNCATE sessions'", home).returncode, 2)

    def test_delete_from_requires_where_in_same_statement(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(run_hook("psql -c 'DELETE FROM users'", home).returncode, 2)
            self.assertEqual(run_hook("psql -c 'DELETE FROM users; SELECT 1 WHERE true'", home).returncode, 2)
            self.assertEqual(run_hook("psql -c 'DELETE FROM users WHERE id = 1'", home).returncode, 0)


if __name__ == "__main__":
    unittest.main()
