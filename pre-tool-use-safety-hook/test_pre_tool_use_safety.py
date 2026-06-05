#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("pre_tool_use_safety.py")


class PreToolUseSafetyHookTest(unittest.TestCase):
    def run_hook(self, command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
        payload = {
            "session_id": "test-session",
            "transcript_path": "/tmp/transcript.jsonl",
            "cwd": "/workspace/project",
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
        }
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.log_content = self.log_path.read_text(encoding="utf-8") if self.log_path.exists() else ""
            return result

    def assert_blocked(self, command: str, expected_reason: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_reason, output["permissionDecisionReason"])
        self.assertIn(command.replace("\n", "\\n"), self.log_content)
        self.assertIn("/workspace/project", self.log_content)

    def assert_allowed(self, command: str, tool_name: str = "Bash") -> None:
        result = self.run_hook(command, tool_name=tool_name)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.log_content, "")

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("sudo rm -fr /tmp/cache", "rm -rf")

    def test_blocks_git_force_push(self) -> None:
        self.assert_blocked("git push origin main --force", "git push --force")
        self.assert_blocked("git push -f", "git push --force")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('mysql -e "TRUNCATE audit_log"', "TRUNCATE")
        self.assert_blocked('psql -c "DELETE FROM accounts"', "DELETE FROM without WHERE")

    def test_allows_safe_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin feature-branch")
        self.assert_allowed('psql -c "DELETE FROM accounts WHERE id = 1"')
        self.assert_allowed("rm build/output.txt")

    def test_ignores_non_bash_tools(self) -> None:
        self.assert_allowed("rm -rf build", tool_name="Read")


if __name__ == "__main__":
    unittest.main()
