import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pre_tool_use_guard as guard


class GuardPatternTests(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertIn("rm", guard.find_block_reason("rm -rf build"))
        self.assertIn("rm", guard.find_block_reason("sudo rm -fr /tmp/demo"))

    def test_blocks_force_push(self):
        self.assertIn("force push", guard.find_block_reason("git push --force origin main"))
        self.assertIn("force push", guard.find_block_reason("git push -f"))

    def test_blocks_drop_and_truncate(self):
        self.assertIn("DROP TABLE", guard.find_block_reason("DROP TABLE users"))
        self.assertIn("TRUNCATE", guard.find_block_reason("truncate table sessions"))

    def test_blocks_delete_without_where(self):
        self.assertIn("DELETE FROM", guard.find_block_reason("DELETE FROM audit_events;"))
        self.assertIsNone(guard.find_block_reason("DELETE FROM audit_events WHERE id = 1;"))

    def test_allows_normal_commands(self):
        self.assertIsNone(guard.find_block_reason("pytest -q"))
        self.assertIsNone(guard.find_block_reason("git push origin main"))
        self.assertIsNone(guard.find_block_reason("SELECT * FROM users"))

    def test_hook_logs_and_denies(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "blocked.log"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf dist"},
                "cwd": "/repo",
            }
            result = subprocess.run(
                [sys.executable, "pre_tool_use_guard.py", "--log", str(log)],
                input=json.dumps(payload),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            response = json.loads(result.stdout)
            decision = response["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            entries = log.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(entries), 1)
            self.assertEqual(json.loads(entries[0])["project_path"], "/repo")

    def test_hook_allows_normal_bash_without_decision(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest -q"},
            "cwd": "/repo",
        }
        result = subprocess.run(
            [sys.executable, "pre_tool_use_guard.py"],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
