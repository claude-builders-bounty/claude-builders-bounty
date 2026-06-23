#!/usr/bin/env python3
"""Unit tests for the destructive Bash guard hook."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / ".claude" / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def payload(command: str, cwd: str = "/tmp/project") -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": cwd,
            "tool_input": {"command": command},
        }
    )


class DestructiveBashGuardTests(unittest.TestCase):
    def run_hook(self, command: str, home: str) -> tuple[int, str]:
        stderr = io.StringIO()
        with patch.dict(os.environ, {"HOME": home, "USERPROFILE": home}, clear=False):
            with patch("sys.stdin", io.StringIO(payload(command))):
                with redirect_stderr(stderr):
                    exit_code = hook.main()
        return exit_code, stderr.getvalue()

    def assert_blocks(self, command: str) -> None:
        with tempfile.TemporaryDirectory() as home:
            exit_code, message = self.run_hook(command, home)
            self.assertEqual(exit_code, 2)
            self.assertIn("blocked", message.lower())
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], command)
            self.assertEqual(log_entry["project_path"], "/tmp/project")

    def test_allows_normal_commands(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            exit_code, message = self.run_hook("git status --short", home)
            self.assertEqual(exit_code, 0)
            self.assertEqual(message, "")
            self.assertFalse((Path(home) / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocks("rm -rf build")
        self.assert_blocks("rm -fr build")

    def test_blocks_force_push(self) -> None:
        self.assert_blocks("git push --force origin main")
        self.assert_blocks("git push -f origin main")

    def test_blocks_dangerous_sql(self) -> None:
        self.assert_blocks("psql -c 'DROP TABLE users'")
        self.assert_blocks("psql -c 'TRUNCATE audit_log'")
        self.assert_blocks("psql -c 'DELETE FROM users'")

    def test_allows_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            exit_code, message = self.run_hook("psql -c 'DELETE FROM users WHERE id = 1'", home)
            self.assertEqual(exit_code, 0)
            self.assertEqual(message, "")


if __name__ == "__main__":
    unittest.main()
