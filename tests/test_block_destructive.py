#!/usr/bin/env python3
"""Tests for the Python PreToolUse destructive-command hook."""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block_destructive.py"
SPEC = importlib.util.spec_from_file_location("block_destructive", str(HOOK))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BLOCKED = [
    ("rm -rf ./dist", "recursive force delete"),
    ("rm -fr build", "recursive force delete"),
    ("rm -r -f tmp", "recursive force delete"),
    ("Remove-Item -Recurse -Force ./out", "recursive force delete"),
    ("DROP TABLE users;", "table drop"),
    ("TRUNCATE TABLE orders", "table truncate"),
    ("git push --force origin main", "forced git push"),
    ("git push -f origin main", "forced git push"),
    ("DELETE FROM users", "unscoped delete"),
]

SAFE = [
    "ls -la",
    "git status --short",
    "DELETE FROM users WHERE id = 1",
    "npm test",
    "python -m pytest -q",
    "mkdir -p build",
]


class ClassificationTests(unittest.TestCase):
    def test_nine_destructive_commands_are_blocked(self):
        for command, expected in BLOCKED:
            with self.subTest(command=command):
                self.assertEqual(MODULE.classify(command), expected)

    def test_six_normal_commands_are_allowed(self):
        for command in SAFE:
            with self.subTest(command=command):
                self.assertIsNone(MODULE.classify(command))

    def test_where_in_a_different_statement_does_not_excuse_delete(self):
        self.assertEqual(
            MODULE.classify("DELETE FROM users; SELECT 1 WHERE id = 1"),
            "unscoped delete",
        )

    def test_mixed_statement_blocks_on_the_dangerous_part(self):
        self.assertEqual(MODULE.classify("echo start && rm -rf dist"), "recursive force delete")


class HookBehaviourTests(unittest.TestCase):
    def run_hook(self, payload):
        old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin = io.StringIO(json.dumps(payload))
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = MODULE.main()
        finally:
            sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr
        return code, out.getvalue(), err.getvalue()

    def test_block_writes_log_and_denies(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CLAUDE_HOOK_LOG"] = str(Path(tmp) / "blocked.log")
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf ./dist"},
                "cwd": "/work/project",
            }
            code, out, err = self.run_hook(payload)
            self.assertEqual(code, 2)
            self.assertIn("permissionDecision", out)
            self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("recursive force delete", err)

            lines = Path(os.environ["CLAUDE_HOOK_LOG"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["attempted_command"], "rm -rf ./dist")
            self.assertEqual(entry["project_path"], "/work/project")
            self.assertEqual(entry["matched_pattern"], "recursive force delete")
            self.assertTrue(entry["timestamp"].endswith("+00:00"))
            del os.environ["CLAUDE_HOOK_LOG"]

    def test_safe_command_is_silent_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CLAUDE_HOOK_LOG"] = str(Path(tmp) / "blocked.log")
            payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": "/work"}
            code, out, err = self.run_hook(payload)
            self.assertEqual((code, out, err), (0, "", ""))
            self.assertFalse(Path(os.environ["CLAUDE_HOOK_LOG"]).exists())
            del os.environ["CLAUDE_HOOK_LOG"]

    def test_non_shell_tools_are_ignored(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "DROP TABLE users"}}
        self.assertEqual(self.run_hook(payload)[0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
