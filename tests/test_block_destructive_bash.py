import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


class DestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["CLAUDE_HOOKS_DIR"] = temp_dir
            payload = {
                "session_id": "test",
                "transcript_path": "/tmp/transcript.jsonl",
                "cwd": "/workspace/demo",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            log_path = Path(temp_dir) / "blocked.log"
            return result, log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    def assert_blocked(self, command: str, expected_reason: str):
        result, log = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        decision = json.loads(result.stdout)
        output = decision["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_reason, output["permissionDecisionReason"])
        self.assertIn(command, log)
        self.assertIn("/workspace/demo", log)

    def assert_allowed(self, command: str):
        result, log = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(log, "")

    def test_blocks_rm_rf(self):
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("rm -fr dist", "rm -rf")

    def test_blocks_drop_table(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked("DROP TABLE users", "DROP TABLE")

    def test_blocks_git_force_push(self):
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")

    def test_blocks_truncate(self):
        self.assert_blocked('mysql -e "TRUNCATE users"', "TRUNCATE")
        self.assert_blocked("TRUNCATE users", "TRUNCATE")

    def test_blocks_delete_from_without_where(self):
        self.assert_blocked('psql -c "DELETE FROM users"', "DELETE FROM without a WHERE clause")
        self.assert_blocked("DELETE FROM users", "DELETE FROM without a WHERE clause")

    def test_allows_delete_from_with_where(self):
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 123"')

    def test_allows_normal_bash_commands(self):
        self.assert_allowed("npm test")
        self.assert_allowed("git status --short")
        self.assert_allowed("grep 'DROP TABLE' docs/schema.md")


if __name__ == "__main__":
    unittest.main()
