#!/usr/bin/env python3
"""Minimal tests for block-destructive-bash.py."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).with_name("block-destructive-bash.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class DetectionTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self) -> None:
        for command in ["rm -rf build", "rm -fr build", "/bin/rm -r -f build"]:
            self.assertIsNotNone(MODULE.find_block_reason(command))

    def test_allows_normal_commands(self) -> None:
        for command in [
            "npm test",
            "git status",
            "rm old.log",
            "DELETE FROM users WHERE id = 1",
        ]:
            self.assertIsNone(MODULE.find_block_reason(command))

    def test_blocks_force_push_and_sql(self) -> None:
        for command in [
            "git push --force origin main",
            "git push -f origin main",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM users'",
        ]:
            self.assertIsNotNone(MODULE.find_block_reason(command))

    def test_blocks_nested_shell(self) -> None:
        self.assertIsNotNone(MODULE.find_block_reason("bash -c 'rm -rf build'"))


class HookIoTests(unittest.TestCase):
    def test_denies_with_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            event = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
                "cwd": temp_dir,
            }
            proc = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
