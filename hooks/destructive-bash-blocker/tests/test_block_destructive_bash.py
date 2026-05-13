#!/usr/bin/env python3
"""Regression tests for the destructive Bash blocker hook."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "block_destructive_bash.py"


spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def payload(command: str) -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
    )


class BlockReasonTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked = {
            "rm -rf dist": "recursive force delete",
            "sudo rm -fr /tmp/demo": "recursive force delete",
            "git push --force origin main": "forced git push",
            "git push -f": "forced git push",
            'psql -c "DROP TABLE users"': "DROP TABLE statement",
            'mysql -e "TRUNCATE TABLE audit_log"': "TRUNCATE statement",
            'psql -c "DELETE FROM users"': "DELETE FROM without WHERE clause",
        }
        for command, reason in blocked.items():
            with self.subTest(command=command):
                self.assertEqual(hook.block_reason(command), reason)

    def test_allows_safe_commands(self) -> None:
        allowed = [
            "rm -r build",
            "rm -f report.txt",
            "git push origin main",
            'psql -c "DELETE FROM users WHERE id = 1"',
            "python3 -m pytest",
            "truncate -s 0 debug.log",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(hook.block_reason(command))


class HookProcessTests(unittest.TestCase):
    def test_denied_command_emits_json_and_writes_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=payload("rm -rf dist"),
                text=True,
                capture_output=True,
                env={"HOME": tmp},
                check=True,
            )

            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("recursive force delete", decision["permissionDecisionReason"])

            log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["command"], "rm -rf dist")
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")

    def test_safe_command_has_no_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=payload("git status --short"),
                text=True,
                capture_output=True,
                env={"HOME": tmp},
                check=True,
            )

            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(tmp) / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
