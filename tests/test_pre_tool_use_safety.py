import importlib.util
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "pre_tool_use_safety.py"
spec = importlib.util.spec_from_file_location("pre_tool_use_safety", HOOK_PATH)
assert spec is not None
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


class SafetyHookTest(unittest.TestCase):
    def test_blocks_required_destructive_patterns(self):
        blocked_commands = [
            "rm -rf build",
            "sudo rm -fr /tmp/app",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push --force-with-lease origin feature",
            "git push -f origin main",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM users;'",
        ]

        for command in blocked_commands:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.block_reason(command))

    def test_allows_normal_commands_and_delete_with_where(self):
        allowed_commands = [
            "npm test",
            "git status --short",
            "git push origin main",
            "python3 -m pytest",
            "psql -c 'DELETE FROM users WHERE id = 1;'",
            "rm -r build",
        ]

        for command in allowed_commands:
            with self.subTest(command=command):
                self.assertIsNone(hook.block_reason(command))

    def test_denies_and_logs_blocked_bash_event(self):
        with tempfile.TemporaryDirectory() as home:
            event = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
                "cwd": "/tmp/demo-project",
            }
            stdin = StringIO(json.dumps(event))
            stdout = StringIO()
            with patch.object(sys, "stdin", stdin), patch.object(hook, "LOG_PATH", Path(home) / ".claude" / "hooks" / "blocked.log"), redirect_stdout(stdout):
                exit_code = hook.main()

            self.assertEqual(exit_code, 0)
            response = json.loads(stdout.getvalue())
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])

            log_lines = (Path(home) / ".claude" / "hooks" / "blocked.log").read_text().splitlines()
            self.assertEqual(len(log_lines), 1)
            log_entry = json.loads(log_lines[0])
            self.assertEqual(log_entry["attempted_command"], "rm -rf build")
            self.assertEqual(log_entry["project_path"], "/tmp/demo-project")
            self.assertIn("timestamp", log_entry)

    def test_non_bash_or_allowed_bash_event_is_silent(self):
        events = [
            {"tool_name": "Read", "tool_input": {"file_path": "README.md"}},
            {"tool_name": "Bash", "tool_input": {"command": "npm test"}},
        ]
        with tempfile.TemporaryDirectory() as home:
            for event in events:
                stdout = StringIO()
                with patch.object(sys, "stdin", StringIO(json.dumps(event))), patch.object(hook, "LOG_PATH", Path(home) / ".claude" / "hooks" / "blocked.log"), redirect_stdout(stdout):
                    self.assertEqual(hook.main(), 0)
                self.assertEqual(stdout.getvalue(), "")
            self.assertFalse((Path(home) / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
