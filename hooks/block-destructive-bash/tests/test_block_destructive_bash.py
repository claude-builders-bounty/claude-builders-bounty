#!/usr/bin/env python3
"""Tests for block_destructive_bash.py — run with `python3 -m unittest discover tests`."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "block_destructive_bash.py"

MUST_BLOCK = [
    "rm -rf /",
    "rm -rf build/",
    "rm -fr ./dist",
    "rm -r -f node_modules",
    "sudo rm -rf /var/log",
    "cd /tmp && rm -rf cache",
    "sqlite3 app.db 'DROP TABLE users'",
    "mysql -e 'drop database production'",
    "psql -c 'TRUNCATE TABLE orders'",
    "sqlite3 app.db 'DELETE FROM users'",
    "sqlite3 app.db 'DELETE FROM users; DELETE FROM items WHERE id = 1'",
    "git push --force origin main",
    "git push -f origin main",
    "git push origin +main",
]

MUST_ALLOW = [
    "ls -la",
    "rm file.txt",
    "rm -r ./tmp-dir",
    "rm -f stale.lock",
    "git status",
    "git push origin main",
    "git push --force-with-lease origin feature",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 3'",
    "sqlite3 app.db 'SELECT * FROM users'",
    "truncate -s 0 app.log",
    "npm test",
    "python3 -c 'print(1)'",
]


def run_check(command: str, env: dict | None = None) -> tuple[int, str]:
    e = dict(os.environ)
    e.pop("BLOCK_DESTRUCTIVE_BASH_ALLOW", None)
    if env:
        e.update(env)
    proc = subprocess.run(
        [sys.executable, str(HOOK), "--check", command],
        capture_output=True,
        text=True,
        env=e,
        timeout=30,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def run_hook_stdin(payload: dict, env: dict | None = None) -> tuple[int, str]:
    e = dict(os.environ)
    e.pop("BLOCK_DESTRUCTIVE_BASH_ALLOW", None)
    if env:
        e.update(env)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=e,
        timeout=30,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


class BlockedPatterns(unittest.TestCase):
    def test_blocks_destructive_commands(self):
        for command in MUST_BLOCK:
            with self.subTest(command=command):
                code, out = run_check(command)
                self.assertEqual(code, 2, f"expected block for: {command} -> {out}")
                self.assertIn("DENY", out)

class AllowedCommands(unittest.TestCase):
    def test_allows_normal_commands(self):
        for command in MUST_ALLOW:
            with self.subTest(command=command):
                code, out = run_check(command)
                self.assertEqual(code, 0, f"false positive for: {command} -> {out}")
                self.assertEqual(out.splitlines()[0], "ALLOW")


class HookProtocol(unittest.TestCase):
    def test_denies_via_json_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "blocked.log"
            env = {"BLOCK_DESTRUCTIVE_BASH_LOG": str(log)}
            code, out = run_hook_stdin(
                {
                    "session_id": "test",
                    "cwd": "/repo",
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf /tmp/x"},
                },
                env,
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])

            lines = log.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["rule"], "rm_rf")
            self.assertEqual(record["cwd"], "/repo")
            self.assertEqual(record["command"], "rm -rf /tmp/x")
            self.assertTrue(record["ts"])

    def test_allows_silently(self):
        code, out = run_hook_stdin(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "npm run build"},
            }
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_ignores_other_tools(self):
        code, out = run_hook_stdin(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "/tmp/x", "content": "rm -rf /"},
            }
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_malformed_input_fails_open(self):
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json at all",
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)

    def test_allowlist_env(self):
        code, out = run_check(
            "rm -rf node_modules", env={"BLOCK_DESTRUCTIVE_BASH_ALLOW": r"rm -rf node_modules"}
        )
        self.assertEqual(code, 0, out)

    def test_exit2_mode_for_old_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "BLOCK_DESTRUCTIVE_BASH_LOG": str(Path(tmp) / "blocked.log"),
                "BLOCK_DESTRUCTIVE_BASH_MODE": "exit2",
            }
            code, out = run_hook_stdin(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "git push --force origin main"},
                },
                env,
            )
            self.assertEqual(code, 2)
            self.assertIn("BLOCKED", out)


if __name__ == "__main__":
    unittest.main()
