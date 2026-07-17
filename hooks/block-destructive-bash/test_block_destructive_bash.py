#!/usr/bin/env python3
"""Drive the real hook entrypoint — no reimplementation of block rules in the test."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block_destructive_bash.py"


def run_hook(command: str, cwd: str, log: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(HOOK),
            "--command",
            command,
            "--cwd",
            cwd,
            "--log",
            str(log),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class BlockDestructiveBashTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "blocked.log"
        self.cwd = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_allows_normal_commands(self):
        for cmd in ("ls -la", "git status", "rm notes.txt", "echo hello"):
            with self.subTest(cmd=cmd):
                r = run_hook(cmd, self.cwd, self.log)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_blocks_rm_rf_and_logs(self):
        r = run_hook("rm -rf /tmp/danger", self.cwd, self.log)
        self.assertEqual(r.returncode, 2)
        self.assertIn("BLOCKED", r.stderr)
        self.assertTrue(self.log.is_file())
        line = self.log.read_text(encoding="utf-8")
        self.assertIn("rm -rf /tmp/danger", line)
        self.assertIn(self.cwd, line)

    def test_blocks_git_force_push(self):
        r = run_hook("git push --force origin main", self.cwd, self.log)
        self.assertEqual(r.returncode, 2)
        self.assertIn("force", r.stderr.lower())

    def test_blocks_sql_destructive(self):
        for cmd in (
            "sqlite3 db 'DROP TABLE users'",
            "psql -c 'TRUNCATE TABLE sessions'",
            "mysql -e 'DELETE FROM users'",
        ):
            with self.subTest(cmd=cmd):
                r = run_hook(cmd, self.cwd, self.log)
                self.assertEqual(r.returncode, 2, r.stderr)

    def test_allows_delete_with_where(self):
        r = run_hook("mysql -e \"DELETE FROM users WHERE id=1\"", self.cwd, self.log)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_stdin_json_bash_payload(self):
        payload = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf ./dist"},
                "cwd": self.cwd,
            }
        )
        r = subprocess.run(
            [sys.executable, str(HOOK), "--log", str(self.log)],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 2, r.stderr)


if __name__ == "__main__":
    unittest.main()
