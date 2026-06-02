#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "destructive-command-guard.py"


class DestructiveCommandGuardTest(unittest.TestCase):
    def run_hook(self, command: str, home: str | None = None) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        env = os.environ.copy()
        if home:
            env["HOME"] = home
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def assert_denied(self, command: str, reason_part: str) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(command, home)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn(reason_part, decision["permissionDecisionReason"])
            log = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            self.assertIn(command, log.read_text(encoding="utf-8"))

    def test_allows_normal_bash_command(self) -> None:
        result = self.run_hook("npm test")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocks_rm_rf_and_combined_flags(self) -> None:
        self.assert_denied("rm -rf dist", "recursive forced removal")
        self.assert_denied("rm -fr build", "recursive forced removal")

    def test_blocks_force_pushes(self) -> None:
        self.assert_denied("git push --force origin main", "force-pushing")
        self.assert_denied("git push origin main --force-with-lease", "force-pushing")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_denied("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_denied("mysql -e 'TRUNCATE audit_log'", "TRUNCATE")
        self.assert_denied("psql -c 'DELETE FROM users'", "DELETE FROM without a WHERE")

    def test_allows_delete_with_where_clause(self) -> None:
        result = self.run_hook("psql -c 'DELETE FROM sessions WHERE expires_at < now()'")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
