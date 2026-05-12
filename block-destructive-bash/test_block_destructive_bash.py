import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).with_name("block-destructive-bash.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


class BlockDestructiveBashTests(unittest.TestCase):
    def test_allows_normal_commands(self):
        self.assertIsNone(hook.block_reason("npm test"))
        self.assertIsNone(hook.block_reason("git push origin feature-branch"))
        self.assertIsNone(hook.block_reason("DELETE FROM users WHERE id = 1"))
        self.assertIsNone(hook.block_reason("rg 'DELETE FROM' docs"))
        self.assertIsNone(hook.block_reason("echo 'DROP TABLE users'"))

    def test_blocks_recursive_force_rm(self):
        self.assertIsNotNone(hook.block_reason("rm -rf build"))
        self.assertIsNotNone(hook.block_reason("rm -fr ./tmp"))
        self.assertIsNotNone(hook.block_reason("rm -r -f ./tmp"))
        self.assertIsNotNone(hook.block_reason("rm --recursive --force ./tmp"))
        self.assertIsNotNone(hook.block_reason("sudo rm -Rf /tmp/demo"))

    def test_blocks_force_push(self):
        self.assertIsNotNone(hook.block_reason("git push --force origin main"))
        self.assertIsNotNone(hook.block_reason("git push -f"))
        self.assertIsNotNone(hook.block_reason("git push --force-with-lease origin main"))

    def test_blocks_destructive_sql(self):
        self.assertIsNotNone(hook.block_reason("psql -c 'DROP TABLE users'"))
        self.assertIsNotNone(hook.block_reason("mysql -e 'TRUNCATE sessions'"))
        self.assertIsNotNone(hook.block_reason("sqlite3 app.db 'DELETE FROM users'"))

    def test_pretooluse_denial_logs_attempt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
                "cwd": "/tmp/example-project",
            }
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
                env={**os.environ, "CLAUDE_HOOKS_LOG": str(log_path)},
            )

            response = json.loads(result.stdout)
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm", output["permissionDecisionReason"])

            log_entry = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")
            self.assertEqual(log_entry["command"], "rm -rf build")


if __name__ == "__main__":
    unittest.main()
