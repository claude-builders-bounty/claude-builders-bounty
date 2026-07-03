import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hooks import block_destructive_commands as hook


class CommandClassificationTests(unittest.TestCase):
    def test_blocks_required_dangerous_patterns(self):
        examples = {
            "rm -rf /tmp/scratch": "rm -rf",
            "sudo rm -rf ./build": "rm -rf",
            "DROP TABLE users;": "DROP TABLE",
            "psql -c 'drop table sessions'": "DROP TABLE",
            "git push --force origin main": "git push --force",
            "git push -f origin main": "git push --force",
            "TRUNCATE audit_log;": "TRUNCATE",
            "DELETE FROM accounts": "DELETE FROM without WHERE",
            "DELETE FROM accounts;": "DELETE FROM without WHERE",
        }

        for command, expected_reason in examples.items():
            with self.subTest(command=command):
                decision = hook.classify_command(command)
                self.assertTrue(decision.blocked)
                self.assertIn(expected_reason, decision.reason)

    def test_allows_normal_commands_and_scoped_delete(self):
        examples = [
            "ls -la",
            "python -m unittest",
            "git push origin feature/destructive-hook",
            "rm -r ./build",
            "DELETE FROM accounts WHERE id = 42",
        ]

        for command in examples:
            with self.subTest(command=command):
                decision = hook.classify_command(command)
                self.assertFalse(decision.blocked)


class HookEntrypointTests(unittest.TestCase):
    def test_blocked_command_logs_attempt_and_denies_permission(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "blocked.log"
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf ./important-data"},
                "cwd": "C:/work/project",
            }

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = hook.main(
                    stdin=io.StringIO(json.dumps(payload)),
                    log_path=log_path,
                )

            self.assertEqual(exit_code, 0)
            response = json.loads(stdout.getvalue())
            self.assertEqual(
                response["hookSpecificOutput"]["hookEventName"],
                "PreToolUse",
            )
            self.assertEqual(
                response["hookSpecificOutput"]["permissionDecision"],
                "deny",
            )
            self.assertIn(
                "rm -rf",
                response["hookSpecificOutput"]["permissionDecisionReason"],
            )
            self.assertIn("Blocked destructive command", stderr.getvalue())

            log_line = log_path.read_text(encoding="utf-8")
            self.assertIn("rm -rf ./important-data", log_line)
            self.assertIn("C:/work/project", log_line)
            self.assertRegex(log_line, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_allowed_command_does_not_log_or_emit_permission_decision(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "blocked.log"
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "python -m unittest"},
                "cwd": "C:/work/project",
            }

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = hook.main(
                    stdin=io.StringIO(json.dumps(payload)),
                    log_path=log_path,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")
            self.assertFalse(log_path.exists())

    def test_non_bash_tools_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "blocked.log"
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "rm -rf notes.txt"},
                "cwd": "C:/work/project",
            }

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = hook.main(
                    stdin=io.StringIO(json.dumps(payload)),
                    log_path=log_path,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertFalse(log_path.exists())

    def test_input_with_utf8_bom_is_parsed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "blocked.log"
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "DROP TABLE users"},
                "cwd": "C:/work/project",
            }

            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                exit_code = hook.main(
                    stdin=io.StringIO("\ufeff" + json.dumps(payload)),
                    log_path=log_path,
                )

            self.assertEqual(exit_code, 0)
            response = json.loads(stdout.getvalue())
            self.assertEqual(
                response["hookSpecificOutput"]["permissionDecision"],
                "deny",
            )
            self.assertTrue(log_path.exists())


class LogPathTests(unittest.TestCase):
    def test_default_log_path_uses_claude_hooks_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            previous_home = os.environ.get("HOME")
            try:
                os.environ["HOME"] = tmp_dir
                self.assertEqual(
                    hook.default_log_path(),
                    Path(tmp_dir) / ".claude" / "hooks" / "blocked.log",
                )
            finally:
                if previous_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = previous_home


if __name__ == "__main__":
    unittest.main()
