#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "pre_tool_use_guard.py"


def run_hook(command: str, hooks_dir: Path, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "project_path": "/tmp/example-project",
    }
    env = os.environ.copy()
    env["CLAUDE_HOOKS_DIR"] = str(hooks_dir)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class PreToolUseGuardTests(unittest.TestCase):
    def test_allows_normal_bash_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook("python -m unittest", Path(temp_dir))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_ignores_non_bash_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook("rm -rf ./dist", Path(temp_dir), tool_name="Read")

        self.assertEqual(result.returncode, 0)

    def test_blocks_rm_rf_and_logs_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            hooks_dir = Path(temp_dir)
            result = run_hook("rm -rf ./dist", hooks_dir)
            log_lines = (hooks_dir / "blocked.log").read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.returncode, 2)
        self.assertIn("Blocked destructive Bash command", result.stderr)
        self.assertEqual(len(log_lines), 1)
        self.assertEqual(json.loads(log_lines[0])["command"], "rm -rf ./dist")

    def test_blocks_drop_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook("psql -c 'DROP TABLE users;'", Path(temp_dir))

        self.assertEqual(result.returncode, 2)

    def test_blocks_force_push_but_allows_force_with_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            hooks_dir = Path(temp_dir)
            blocked = run_hook("git push --force origin main", hooks_dir)
            allowed = run_hook("git push --force-with-lease origin main", hooks_dir)

        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(allowed.returncode, 0)

    def test_blocks_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook("psql -c 'TRUNCATE audit_log;'", Path(temp_dir))

        self.assertEqual(result.returncode, 2)

    def test_blocks_delete_from_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            blocked = run_hook("psql -c 'DELETE FROM users;'", Path(temp_dir))
            allowed = run_hook("psql -c 'DELETE FROM users WHERE id = 1;'", Path(temp_dir))

        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(allowed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
