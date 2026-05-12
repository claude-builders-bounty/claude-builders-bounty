#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("destructive-command-guard.py")
spec = importlib.util.spec_from_file_location("guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class DestructiveCommandGuardTest(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked = [
            "rm" + " -rf build",
            "sudo rm" + " -fr /tmp/demo",
            "rm --recursive --force build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f",
            "TRUNCATE TABLE sessions",
            "DELETE FROM accounts",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.dangerous_reason(command))

    def test_allows_normal_commands_and_guarded_delete(self) -> None:
        allowed = [
            "ls -la",
            "git push origin main",
            "rm -r build",
            "DELETE FROM accounts WHERE id = 1",
            "python -m unittest",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.dangerous_reason(command))

    def test_main_returns_structured_deny_response_and_logs_jsonl(self) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git push --force origin main",
                "cwd": "/tmp/project",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            original_log_path = guard.LOG_PATH
            guard.LOG_PATH = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            try:
                stdout = io.StringIO()
                with patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(stdout):
                    exit_code = guard.main()
                self.assertEqual(exit_code, 0)

                response = json.loads(stdout.getvalue())
                hook_output = response["hookSpecificOutput"]
                self.assertEqual(hook_output["hookEventName"], "PreToolUse")
                self.assertEqual(hook_output["permissionDecision"], "deny")
                self.assertIn("git push", hook_output["permissionDecisionReason"])

                log_entry = json.loads(guard.LOG_PATH.read_text().strip())
                self.assertEqual(log_entry["command"], "git push --force origin main")
                self.assertEqual(log_entry["project_path"], "/tmp/project")
                self.assertIn("timestamp", log_entry)
            finally:
                guard.LOG_PATH = original_log_path

    def test_non_bash_payload_is_ignored(self) -> None:
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
        stdout = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(stdout):
            exit_code = guard.main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
