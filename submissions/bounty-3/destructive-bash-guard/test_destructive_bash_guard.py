#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import destructive_bash_guard as guard


class ClassificationTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked = [
            "rm -rf build",
            "sudo rm -fr /tmp/cache",
            "rm -Rf dist",
            "sqlite3 app.db 'DROP TABLE users'",
            "psql -c 'TRUNCATE audit_log'",
            "git push origin main --force",
            "git -C ../repo push origin main --force-with-lease",
            "git push -f origin main",
            "sqlite3 app.db 'DELETE FROM sessions;'",
        ]

        for command in blocked:
            with self.subTest(command=command):
                self.assertTrue(guard.classify_command(command).blocked)

    def test_allows_safe_commands(self) -> None:
        allowed = [
            "ls -la",
            "rm -r build",
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < datetime()'",
            "python3 manage.py migrate",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertFalse(guard.classify_command(command).blocked)


class HookOutputTests(unittest.TestCase):
    def test_denies_bash_command_with_current_hook_schema(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": "/repo",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf dist"},
        }

        with tempfile.TemporaryDirectory() as home:
            script = Path(__file__).with_name("destructive_bash_guard.py")
            result = subprocess.run(
                [sys.executable, str(script)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home, "PATH": ""},
                check=True,
            )

            output = json.loads(result.stdout)
            specific = output["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], "PreToolUse")
            self.assertEqual(specific["permissionDecision"], "deny")
            self.assertIn("rm with recursive and force flags", specific["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["command"], "rm -rf dist")
            self.assertEqual(log_entry["project_path"], "/repo")

    def test_allows_non_bash_without_output(self) -> None:
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {}}
        script = Path(__file__).with_name("destructive_bash_guard.py")
        result = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
