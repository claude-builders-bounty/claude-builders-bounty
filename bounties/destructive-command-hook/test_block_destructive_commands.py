#!/usr/bin/env python3
"""Smoke tests for the destructive command hook."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("block_destructive_commands.py")


spec = importlib.util.spec_from_file_location("hook", SCRIPT)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


class PatternTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self) -> None:
        self.assertEqual(hook.find_violation("rm -rf dist"), "recursive forced removal with rm")
        self.assertEqual(hook.find_violation("sudo rm -fr /tmp/build"), "recursive forced removal with rm")
        self.assertEqual(hook.find_violation("rm -r -f node_modules"), "recursive forced removal with rm")

    def test_blocks_git_force_push(self) -> None:
        self.assertEqual(hook.find_violation("git push --force origin main"), "forced git push")
        self.assertEqual(hook.find_violation("git push -f"), "forced git push")

    def test_blocks_destructive_sql(self) -> None:
        self.assertEqual(hook.find_violation("psql -c 'DROP TABLE users'"), "destructive SQL statement")
        self.assertEqual(hook.find_violation("mysql -e 'TRUNCATE sessions'"), "destructive SQL statement")
        self.assertEqual(hook.find_violation("sqlite3 app.db 'DELETE FROM users'"), "destructive SQL statement")

    def test_allows_safe_commands(self) -> None:
        self.assertIsNone(hook.find_violation("npm test"))
        self.assertIsNone(hook.find_violation("rm -r dist"))
        self.assertIsNone(hook.find_violation("git push origin main"))
        self.assertIsNone(hook.find_violation("psql -c 'DELETE FROM users WHERE id = 1'"))
        self.assertIsNone(hook.find_violation("grep 'DROP TABLE' migrations.sql"))


class HookIOTests(unittest.TestCase):
    def run_hook(self, command: str) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
        with tempfile.TemporaryDirectory() as tmp_home:
            return subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": tmp_home},
                check=False,
            )

    def test_denies_with_json(self) -> None:
        result = self.run_hook("rm -rf dist")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("recursive forced removal", decision["permissionDecisionReason"])

    def test_allows_without_output(self) -> None:
        result = self.run_hook("npm test")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
