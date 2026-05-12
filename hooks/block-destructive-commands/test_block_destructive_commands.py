import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("block_destructive_commands.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_commands", MODULE_PATH)
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


class DestructiveCommandHookTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        cases = {
            "rm -rf build": "rm -rf",
            "git push --force origin main": "git push --force",
            "git push -f origin main": "git push --force",
            "psql -c 'DROP TABLE users'": "DROP TABLE",
            "sqlite3 app.db 'TRUNCATE audit_log'": "TRUNCATE",
            "psql -c 'DELETE FROM users'": "DELETE FROM without WHERE",
        }

        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(hook.destructive_reason(command), expected)

    def test_allows_normal_commands(self):
        allowed = [
            "npm test",
            "git push origin feature-branch",
            "psql -c 'DELETE FROM sessions WHERE expires_at < now()'",
            "rm -r build",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(hook.destructive_reason(command))

    def test_main_outputs_deny_json_and_log(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf build"},
            "cwd": "/tmp/example-project",
        }

        with TemporaryDirectory() as home:
            stdout = io.StringIO()
            with patch("pathlib.Path.home", return_value=Path(home)):
                with patch("sys.stdin", io.StringIO(json.dumps(payload))):
                    with redirect_stdout(stdout):
                        self.assertEqual(hook.main(), 0)

            response = json.loads(stdout.getvalue())
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text().strip())
            self.assertEqual(log_entry["command"], "rm -rf build")
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")


if __name__ == "__main__":
    unittest.main()
