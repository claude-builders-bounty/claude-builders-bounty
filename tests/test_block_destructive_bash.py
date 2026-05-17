from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hooks.block_destructive_bash import detect_block_reason


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks" / "block_destructive_bash.py"


class DetectBlockReasonTests(unittest.TestCase):
    def test_blocks_rm_rf(self) -> None:
        self.assertEqual(detect_block_reason("rm -rf /tmp/demo"), "rm -rf")
        self.assertEqual(detect_block_reason("sudo rm -r -f ./build"), "rm -rf")

    def test_blocks_git_force_push(self) -> None:
        self.assertEqual(
            detect_block_reason("git push origin main --force"),
            "git push --force",
        )

    def test_blocks_sql_dangers(self) -> None:
        self.assertEqual(detect_block_reason("DROP TABLE users;"), "DROP TABLE")
        self.assertEqual(detect_block_reason("TRUNCATE TABLE sessions;"), "TRUNCATE")
        self.assertEqual(
            detect_block_reason("DELETE FROM users;"),
            "DELETE FROM without WHERE",
        )
        self.assertIsNone(detect_block_reason("DELETE FROM users WHERE id = 1;"))

    def test_allows_normal_commands(self) -> None:
        self.assertIsNone(detect_block_reason("git status"))
        self.assertIsNone(detect_block_reason("rm file.txt"))
        self.assertIsNone(detect_block_reason("echo 'rm -rf is dangerous'"))


class HookRuntimeTests(unittest.TestCase):
    def test_blocked_command_logs_and_denies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            env["USERPROFILE"] = temp_home
            env["CLAUDE_PROJECT_DIR"] = "/work/project"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /tmp/demo"},
                "cwd": "/work/project",
            }
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]["permissionDecision"]
            reason = output["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertEqual(decision, "deny")
            self.assertIn("Blocked destructive Bash command", reason)

            log_path = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            logged = json.loads(lines[0])
            self.assertEqual(logged["attempted_command"], "rm -rf /tmp/demo")
            self.assertEqual(logged["project_path"], "/work/project")
            self.assertIn("timestamp", logged)

    def test_normal_command_stays_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            env["USERPROFILE"] = temp_home
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
                "cwd": "/work/project",
            }
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(
                (Path(temp_home) / ".claude" / "hooks" / "blocked.log").exists()
            )


if __name__ == "__main__":
    unittest.main()
