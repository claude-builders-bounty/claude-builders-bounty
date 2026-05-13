import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from hooks import block_destructive_bash as hook


class DetectionTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        cases = {
            "rm -rf /tmp/build": "rm-rf",
            "rm -fr ./dist": "rm-rf",
            "psql -c 'DROP TABLE users'": "drop-table",
            "git push --force origin main": "git-push-force",
            "git push -f": "git-push-force",
            "sqlite3 app.db 'TRUNCATE audit_log'": "truncate",
            "psql -c 'DELETE FROM sessions'": "delete-without-where",
        }
        for command, expected_rule in cases.items():
            with self.subTest(command=command):
                match = hook.detect_destructive_command(command)
                self.assertIsNotNone(match)
                self.assertEqual(match[0], expected_rule)

    def test_allows_normal_bash_commands(self):
        safe_commands = [
            "npm test",
            "git push origin feature-branch",
            "rm build.log",
            "python3 -m pytest",
            "psql -c 'DELETE FROM sessions WHERE expires_at < now()'",
        ]
        for command in safe_commands:
            with self.subTest(command=command):
                self.assertIsNone(hook.detect_destructive_command(command))


class HookRuntimeTests(unittest.TestCase):
    def run_hook(self, payload, home):
        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with patch("sys.stdin", stdin), patch("pathlib.Path.home", return_value=Path(home)), redirect_stdout(stdout):
            code = hook.main()
        return code, stdout.getvalue()

    def test_safe_command_exits_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_hook(
                {"tool_name": "Bash", "tool_input": {"command": "npm test"}, "cwd": "/repo"}, tmp
            )
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertFalse((Path(tmp) / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocked_command_outputs_decision_and_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_hook(
                {"tool_name": "Bash", "tool_input": {"command": "rm -rf dist"}, "cwd": "/repo"}, tmp
            )
            self.assertEqual(code, 0)
            decision = json.loads(out)
            specific = decision["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], "PreToolUse")
            self.assertEqual(specific["permissionDecision"], "deny")
            self.assertIn("rm-rf", specific["permissionDecisionReason"])

            log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log_path.read_text().strip())
            self.assertEqual(record["project_path"], "/repo")
            self.assertEqual(record["command"], "rm -rf dist")
            self.assertEqual(record["rule_id"], "rm-rf")
            self.assertIn("timestamp", record)

    def test_non_bash_tool_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_hook(
                {"tool_name": "Write", "tool_input": {"file_path": "/tmp/x", "content": "rm -rf"}, "cwd": "/repo"}, tmp
            )
            self.assertEqual(code, 0)
            self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
