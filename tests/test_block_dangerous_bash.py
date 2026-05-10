import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / ".claude" / "hooks" / "block-dangerous-bash.py"

spec = importlib.util.spec_from_file_location("block_dangerous_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


class BlockDangerousBashTests(unittest.TestCase):
    def test_normal_commands_are_allowed(self):
        for command in ["git status", "npm test", "rm build.log"]:
            with self.subTest(command=command):
                self.assertIsNone(hook.find_block_reason(command))

    def test_required_patterns_are_blocked(self):
        cases = {
            "rm -rf dist": "rm -rf",
            "DROP TABLE users": "DROP TABLE",
            "git push --force origin main": "git push --force",
            "TRUNCATE TABLE audit_log": "TRUNCATE",
            "DELETE FROM users": "DELETE FROM without WHERE",
        }
        for command, expected_pattern in cases.items():
            with self.subTest(command=command):
                reason = hook.find_block_reason(command)
                self.assertIsNotNone(reason)
                self.assertEqual(reason.pattern, expected_pattern)

    def test_delete_from_with_where_is_allowed(self):
        self.assertIsNone(hook.find_block_reason("DELETE FROM users WHERE id = 1"))

    def test_hook_outputs_deny_json_and_logs_block(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf dist"},
                "cwd": "/tmp/project",
            }
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": home, "USERPROFILE": home},
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], "rm -rf dist")
            self.assertEqual(log_entry["project_path"], "/tmp/project")


if __name__ == "__main__":
    unittest.main()
