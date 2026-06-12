#!/usr/bin/env python3
"""Integration test: run the actual hook against a synthetic PreToolUse
payload delivered on stdin. Verifies exit code, stderr message, and
audit-log entry without needing a real Claude Code installation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOK = Path(__file__).parent / "block-destructive.py"
PYTHON = sys.executable


def run_hook(command: str, *, env: dict | None = None) -> subprocess.CompletedProcess:
    payload = {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/test-project",
    }
    return subprocess.run(
        [PYTHON, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
        timeout=10,
    )


class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Use a per-test log file so parallel runs don't collide.
        self._tmpdir = tempfile.mkdtemp()
        self._log_path = Path(self._tmpdir) / "blocked.log"
        self._env = {"DESTRUCTIVE_HOOK_LOG": str(self._log_path)}

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_blocks_rm_rf(self):
        r = run_hook("rm -rf /tmp/whatever", env=self._env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("BLOCKED", r.stderr)
        self.assertIn("rm --recursive --force", r.stderr)
        self.assertTrue(self._log_path.exists())
        entry = self._log_path.read_text()
        self.assertIn("rm -rf /tmp/whatever", entry)
        self.assertIn("/tmp/test-project", entry)

    def test_blocks_force_push(self):
        r = run_hook("git push --force origin main", env=self._env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("git push --force", r.stderr)

    def test_allows_safe_rm(self):
        r = run_hook("rm -f file.txt", env=self._env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, "")
        self.assertFalse(self._log_path.exists())

    def test_allows_safe_git(self):
        r = run_hook("git push origin main", env=self._env)
        self.assertEqual(r.returncode, 0)
        self.assertFalse(self._log_path.exists())

    def test_blocks_drop_table_in_psql(self):
        r = run_hook("psql -c 'DROP TABLE users'", env=self._env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("DROP <object>", r.stderr)

    def test_blocks_truncate(self):
        r = run_hook("TRUNCATE TABLE events", env=self._env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("TRUNCATE", r.stderr)

    def test_blocks_delete_without_where(self):
        r = run_hook("DELETE FROM users;", env=self._env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("DELETE FROM without WHERE", r.stderr)

    def test_allows_delete_with_where(self):
        r = run_hook("DELETE FROM users WHERE id = 1", env=self._env)
        self.assertEqual(r.returncode, 0)

    def test_ignores_non_bash_tool(self):
        # Even if the command looks dangerous, the hook only fires on Bash.
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/etc/passwd", "content": "x"},
            "cwd": "/tmp",
        }
        r = subprocess.run(
            [PYTHON, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**os.environ, **self._env},
            timeout=10,
        )
        self.assertEqual(r.returncode, 0)

    def test_fails_open_on_bad_json(self):
        r = subprocess.run(
            [PYTHON, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            env={**os.environ, **self._env},
            timeout=10,
        )
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
