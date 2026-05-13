#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "block_destructive_commands.py"

spec = importlib.util.spec_from_file_location("block_destructive_commands", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


class BlockDestructiveCommandsTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked_commands = [
            "rm -rf build/",
            "sudo rm -fr /tmp/demo",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "TRUNCATE audit_log;",
            "DELETE FROM users;",
        ]
        for command in blocked_commands:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.find_block_reason(command))

    def test_allows_normal_bash_commands(self) -> None:
        allowed_commands = [
            "npm test",
            "git push origin feature-branch",
            "rm -r build",
            "python3 scripts/generate.py",
            "SELECT * FROM users;",
            "DELETE FROM sessions WHERE id = 1;",
        ]
        for command in allowed_commands:
            with self.subTest(command=command):
                self.assertIsNone(hook.find_block_reason(command))

    def test_denies_and_logs_destructive_bash_command(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/demo"},
            "cwd": "/repo/path",
        }
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            response = json.loads(result.stdout)
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("rm -rf /tmp/demo", log_text)
            self.assertIn("/repo/path", log_text)

    def test_non_destructive_command_has_no_output(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "npm test"},
            "cwd": "/repo/path",
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
