import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / ".claude" / "hooks" / "destructive_bash_guard.py"
INSTALLER_PATH = ROOT / "bounty-3" / "install.py"

spec = importlib.util.spec_from_file_location("guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    def test_required_patterns_are_blocked(self):
        blocked = [
            "rm -rf build/",
            "rm -fr build/",
            "rm -r -f build/",
            "sudo rm -rf /tmp/demo",
            "env FOO=1 rm --recursive --force build/",
            "DROP TABLE users;",
            "psql -c 'DROP TABLE users;'",
            "sqlite3 app.db 'TRUNCATE TABLE audit_log;'",
            "git push --force origin main",
            "git push -f origin main",
            "git -C repo push --force-with-lease origin main",
            "DELETE FROM users;",
            "psql -c 'DELETE FROM sessions'",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_nested_shell_execution_is_blocked(self):
        for command in [
            "bash -c 'rm -rf /tmp/demo'",
            "sh -c \"git push --force origin main\"",
        ]:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_normal_commands_are_allowed(self):
        allowed = [
            "rm build/output.txt",
            "git push origin feature/x",
            "git push --force-if-includes origin main",
            "psql -c 'DELETE FROM users WHERE id = 42;'",
            "echo hello",
            "python -m pytest",
            "ls -la",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command))

    def test_harmless_mentions_do_not_trigger(self):
        allowed = [
            'echo "rm -rf /"',
            'printf "git push --force origin main"',
            'grep "DROP TABLE" schema.sql',
            'echo "TRUNCATE TABLE events"',
            'printf "DELETE FROM users"',
            'psql -c "SELECT \'DROP TABLE users\';"',
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command))

    def test_delete_where_is_checked_per_statement(self):
        self.assertIsNotNone(
            guard.blocked_reason("psql -c 'DELETE FROM a WHERE id=1; DELETE FROM b;'")
        )
        self.assertIsNone(
            guard.blocked_reason(
                "psql -c 'DELETE FROM a WHERE id=1; DELETE FROM b WHERE id=2;'"
            )
        )

    def test_comments_are_ignored(self):
        self.assertIsNone(guard.blocked_reason("# rm -rf /"))
        self.assertIsNone(guard.blocked_reason("echo safe # git push --force"))

    def test_blocked_attempt_is_logged_as_jsonl_and_denied(self):
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "blocked.log"
            event = {
                "tool_name": "Bash",
                "cwd": "/tmp/example-project",
                "tool_input": {"command": "git push --force origin main"},
            }
            with patch.object(guard, "LOG_PATH", log_path), \
                 patch("sys.stdin", io.StringIO(json.dumps(event))), \
                 patch("sys.stdout", new_callable=io.StringIO) as stdout:
                rc = guard.main()

            self.assertEqual(rc, 0)
            response = json.loads(stdout.getvalue())
            specific = response["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], "PreToolUse")
            self.assertEqual(specific["permissionDecision"], "deny")
            self.assertIn("Blocked destructive command", specific["permissionDecisionReason"])

            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["command"], "git push --force origin main")
            self.assertEqual(record["project_path"], "/tmp/example-project")
            self.assertTrue(record["timestamp"])
            self.assertTrue(record["reason"])

    def test_non_bash_tool_is_ignored(self):
        event = {"tool_name": "Read", "tool_input": {"command": "rm -rf /tmp/x"}}
        with patch("sys.stdin", io.StringIO(json.dumps(event))), \
             patch("sys.stdout", new_callable=io.StringIO) as stdout:
            rc = guard.main()
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_normal_bash_command_is_ignored(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "echo safe"}}
        with patch("sys.stdin", io.StringIO(json.dumps(event))), \
             patch("sys.stdout", new_callable=io.StringIO) as stdout:
            rc = guard.main()
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_installer_is_idempotent_and_preserves_settings(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            claude = home / ".claude"
            claude.mkdir()
            settings = claude / "settings.json"
            settings.write_text(
                json.dumps({"permissions": {"allow": ["Read"]}}),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["HOME"] = str(home)

            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(INSTALLER_PATH)],
                    cwd=ROOT,
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            installed_hook = claude / "hooks" / "destructive_bash_guard.py"
            self.assertTrue(installed_hook.exists())

            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(data["permissions"], {"allow": ["Read"]})
            entries = data["hooks"]["PreToolUse"]
            matching = [
                entry for entry in entries
                if any(
                    hook.get("command") == str(installed_hook)
                    for hook in entry.get("hooks", [])
                )
            ]
            self.assertEqual(len(matching), 1)


if __name__ == "__main__":
    unittest.main()
