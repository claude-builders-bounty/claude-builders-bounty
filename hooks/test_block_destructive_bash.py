#!/usr/bin/env python3

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).parent / "block_destructive_bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
HOOK = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(HOOK)


class DestructiveBashHookTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked = [
            "rm -rf build",
            "rm -fr build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "psql -c 'TRUNCATE audit_log'",
            "psql -c 'DELETE FROM users'",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(HOOK.classify_command(command))

    def test_allows_normal_commands(self):
        allowed = [
            "git status",
            "npm test",
            "python3 -m unittest",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "grep -R 'DROP TABLE' docs/",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(HOOK.classify_command(command))

    def test_cli_denies_and_logs_blocked_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
                "cwd": "/tmp/project",
            }
            env = os.environ.copy()
            env["CLAUDE_BLOCKED_LOG"] = str(log_path)
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            decision = response["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["command"], "rm -rf build")
            self.assertEqual(log_entry["project_path"], "/tmp/project")
            self.assertIn("timestamp", log_entry)

    def test_cli_allows_normal_command_without_output(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "cwd": "/tmp/project",
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
