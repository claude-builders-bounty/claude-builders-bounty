import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("block_destructive_bash.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", SCRIPT)
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


class DestructiveBashHookTest(unittest.TestCase):
    def assert_blocked(self, command):
        blocked, rule, message = hook.check_command(command)
        self.assertTrue(blocked, command)
        self.assertTrue(rule)
        self.assertTrue(message)

    def test_blocks_required_patterns(self):
        self.assert_blocked("rm -rf dist")
        self.assert_blocked("psql -c 'DROP TABLE users'")
        self.assert_blocked("git push origin main --force")
        self.assert_blocked("git push --force-with-lease")
        self.assert_blocked("psql -c 'TRUNCATE audit_log'")
        self.assert_blocked("mysql -e 'DELETE FROM customers;'")

    def test_allows_normal_commands_and_safe_delete(self):
        for command in [
            "npm test",
            "git push origin main",
            "rm -r dist",
            "psql -c 'DELETE FROM customers WHERE id = 7;'",
        ]:
            blocked, _, _ = hook.check_command(command)
            self.assertFalse(blocked, command)

    def test_main_logs_blocked_attempt(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/example"},
            "cwd": "/repo/path",
        }
        with tempfile.TemporaryDirectory() as home:
            output = io.StringIO()
            with patch.dict(os.environ, {"HOME": home, "USERPROFILE": home}), patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(output):
                self.assertEqual(hook.main(), 0)

            response = json.loads(output.getvalue())
            self.assertEqual(response["decision"], "block")
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["attempted_command"], "rm -rf /tmp/example")
            self.assertEqual(entry["project_path"], "/repo/path")


if __name__ == "__main__":
    unittest.main()
