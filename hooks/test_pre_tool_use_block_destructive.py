#!/usr/bin/env python3
"""Unit tests for the destructive-command PreToolUse hook."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

HOOK_PATH = Path(__file__).resolve().parent / "pre_tool_use_block_destructive.py"
spec = importlib.util.spec_from_file_location("hook", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def run_hook(command: str, tool_name: str = "Bash", cwd: str = "/tmp/proj") -> tuple[int, str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "cwd": cwd,
        "tool_input": {"command": command},
    }
    stdin = io.StringIO(json.dumps(payload))
    stderr = io.StringIO()
    with mock.patch.object(sys, "stdin", stdin), redirect_stderr(stderr):
        code = hook.main()
    return code, stderr.getvalue()


class BlockDestructiveHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.log = Path(self._tmp.name) / "blocked.log"
        self._log_patch = mock.patch.object(hook, "LOG_PATH", self.log)
        self._log_patch.start()

    def tearDown(self) -> None:
        self._log_patch.stop()
        self._tmp.cleanup()

    def assert_blocked(self, command: str, rule: str) -> None:
        code, err = run_hook(command)
        self.assertEqual(code, 2, msg=f"expected block for: {command!r}\nstderr={err}")
        self.assertIn(rule, err)
        self.assertTrue(self.log.exists())
        self.assertIn(rule, self.log.read_text(encoding="utf-8"))
        self.assertIn("BLOCKED", err)

    def assert_allowed(self, command: str) -> None:
        code, err = run_hook(command)
        self.assertEqual(code, 0, msg=f"expected allow for: {command!r}\nstderr={err}")
        self.assertEqual(err, "")

    # --- blocked ---
    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf /tmp/build", "rm_rf")
        self.assert_blocked("rm -fr node_modules", "rm_rf")
        self.assert_blocked("cd /tmp && rm -rf ./dist", "rm_rf")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users;'", "drop_table")
        self.assert_blocked("sqlite3 app.db 'drop table logs'", "drop_table")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked("mysql -e 'TRUNCATE TABLE sessions'", "truncate")
        self.assert_blocked("psql -c 'truncate audit_log'", "truncate")

    def test_blocks_delete_from_without_where(self) -> None:
        self.assert_blocked("sqlite3 x.db 'DELETE FROM users'", "delete_from_no_where")
        self.assert_blocked("psql -c \"delete from events;\"", "delete_from_no_where")

    def test_blocks_git_push_force(self) -> None:
        self.assert_blocked("git push --force origin main", "git_push_force")
        self.assert_blocked("git push -f", "git_push_force")
        self.assert_blocked("git push --force-with-lease origin master", "git_push_force")

    # --- allowed ---
    def test_allows_safe_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("git status")
        self.assert_allowed("git push origin feature/x")
        self.assert_allowed("rm file.txt")
        self.assert_allowed("rm -f tmp.log")
        self.assert_allowed("ls -la")

    def test_allows_delete_from_with_where(self) -> None:
        self.assert_allowed("sqlite3 x.db 'DELETE FROM users WHERE id = 1'")

    def test_ignores_non_bash_tools(self) -> None:
        code, _ = run_hook("rm -rf /", tool_name="Write")
        self.assertEqual(code, 0)

    def test_allows_empty_payload(self) -> None:
        stdin = io.StringIO("")
        with mock.patch.object(sys, "stdin", stdin):
            self.assertEqual(hook.main(), 0)

    def test_log_contains_timestamp_and_cwd(self) -> None:
        run_hook("rm -rf ./out", cwd="/home/dev/project")
        body = self.log.read_text(encoding="utf-8")
        self.assertIn("/home/dev/project", body)
        self.assertIn("rm -rf ./out", body)


if __name__ == "__main__":
    unittest.main()
