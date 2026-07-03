import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("block_destructive_bash.py")
spec = importlib.util.spec_from_file_location("block_destructive_bash", MODULE_PATH)
blocker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blocker)


class DestructiveBashBlockerTests(unittest.TestCase):
    def assert_blocked(self, command, label):
        reason = blocker.destructive_reason(command)
        self.assertIsNotNone(reason)
        self.assertIn(label, reason)

    def assert_allowed(self, command):
        self.assertIsNone(blocker.destructive_reason(command))

    def test_blocks_rm_rf(self):
        self.assert_blocked("rm -rf dist", "rm -rf")
        self.assert_blocked("rm -fr ./tmp", "rm -rf")
        self.assert_blocked("echo ok && rm -rf /tmp/build", "rm -rf")

    def test_blocks_force_push(self):
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push --force-with-lease origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")

    def test_blocks_sql_destructive_patterns(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("mysql -e 'TRUNCATE TABLE audit_log'", "TRUNCATE")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM sessions'", "DELETE FROM without WHERE")

    def test_allows_normal_commands(self):
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm -r tmp")
        self.assert_allowed("truncate -s 0 app.log")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM sessions WHERE id = 1'")
        self.assert_allowed("npm test")

    def test_main_denies_and_logs_blocked_bash_command(self):
        payload = {
            "tool_name": "Bash",
            "cwd": "/workspace/project",
            "tool_input": {"command": "echo before && rm -rf dist"},
        }

        with tempfile.TemporaryDirectory() as temp_home:
            stdin = io.StringIO(json.dumps(payload))
            stdout = io.StringIO()
            with patch.dict(os.environ, {"HOME": temp_home}, clear=False):
                with patch.object(blocker.Path, "home", return_value=Path(temp_home)):
                    with patch("sys.stdin", stdin), patch("sys.stdout", stdout):
                        exit_code = blocker.main()

            self.assertEqual(exit_code, 0)
            output = json.loads(stdout.getvalue())
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_path = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["project_path"], "/workspace/project")
            self.assertEqual(log_entry["command"], "echo before && rm -rf dist")
            self.assertIn("rm -rf", log_entry["reason"])
            self.assertIn("timestamp", log_entry)


if __name__ == "__main__":
    unittest.main()
