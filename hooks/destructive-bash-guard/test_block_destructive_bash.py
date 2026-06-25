#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "block_destructive_bash.py"


def run_hook(command: str, log_path: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {
            "command": command,
        },
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    env["CLAUDE_HOOKS_BLOCKED_LOG"] = str(log_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashGuardTests(unittest.TestCase):
    def test_allows_normal_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("npm test && git status --short", Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_blocks_rm_rf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "blocked.log"
            result = run_hook("sudo rm -Rf build", log)
            self.assertEqual(result.returncode, 2)
            self.assertIn("recursive and force", result.stderr)
            entry = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(entry["attempted_command"], "sudo rm -Rf build")
            self.assertEqual(entry["project_path"], "/tmp/example-project")

    def test_blocks_drop_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("sqlite3 app.db 'DROP TABLE users;'", Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DROP TABLE", result.stderr)

    def test_blocks_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("psql -c 'TRUNCATE sessions;'", Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 2)
        self.assertIn("TRUNCATE", result.stderr)

    def test_blocks_delete_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("sqlite3 app.db 'DELETE FROM users;'", Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DELETE FROM without a WHERE", result.stderr)

    def test_allows_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("sqlite3 app.db 'DELETE FROM users WHERE id = 1;'", Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 0)

    def test_allows_multiline_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            command = "sqlite3 app.db 'DELETE FROM users\nWHERE id = 1;'"
            result = run_hook(command, Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 0)

    def test_blocks_force_push(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook("git push origin main --force-with-lease", Path(directory) / "blocked.log")
        self.assertEqual(result.returncode, 2)
        self.assertIn("force-pushing", result.stderr)


if __name__ == "__main__":
    unittest.main()
