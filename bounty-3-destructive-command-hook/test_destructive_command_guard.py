import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "destructive-command-guard.py"

spec = importlib.util.spec_from_file_location("guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DestructiveCommandGuardTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self):
        self.assertIsNotNone(guard.blocked_reason("rm -rf ./dist"))
        self.assertIsNotNone(guard.blocked_reason("rm -fr ./dist"))
        self.assertIsNotNone(
            guard.blocked_reason("rm --recursive --force ./dist")
        )

    def test_blocks_force_push_variants(self):
        self.assertIsNotNone(guard.blocked_reason("git push --force origin main"))
        self.assertIsNotNone(guard.blocked_reason("git push -f origin main"))
        self.assertIsNotNone(
            guard.blocked_reason("git push --force-with-lease origin main")
        )

    def test_blocks_drop_table_and_truncate(self):
        self.assertIsNotNone(guard.blocked_reason("psql -c 'DROP TABLE users'"))
        self.assertIsNotNone(guard.blocked_reason("mysql -e 'TRUNCATE sessions'"))

    def test_blocks_delete_without_where(self):
        self.assertIsNotNone(guard.blocked_reason("DELETE FROM users;"))
        self.assertIsNotNone(guard.blocked_reason("psql -c 'delete from sessions'"))

    def test_allows_delete_with_where(self):
        self.assertIsNone(guard.blocked_reason("DELETE FROM users WHERE id = 1;"))

    def test_allows_normal_commands(self):
        self.assertIsNone(guard.blocked_reason("npm test"))
        self.assertIsNone(guard.blocked_reason("git push origin feature-branch"))
        self.assertIsNone(guard.blocked_reason("rm -r ./dist"))

    def test_hook_json_response_blocks_bash_payload(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf ./dist"},
            "cwd": "/tmp/project",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["CLAUDE_HOOKS_BLOCKED_LOG"] = str(Path(temp_dir) / "blocked.log")
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        hook_output = response["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn(
            "Blocked destructive Bash command",
            hook_output["permissionDecisionReason"],
        )

    def test_hook_json_response_approves_safe_payload(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "npm test"}}
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
