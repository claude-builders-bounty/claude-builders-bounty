#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("block_hook.py")


class HookTests(unittest.TestCase):
    def run_hook(self, command: str, *, tool_name: str = "Bash", home: str | None = None):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        env = os.environ.copy()
        if home is not None:
            env["HOME"] = home
        return subprocess.run(
            ["python3", str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_required_destructive_patterns_are_blocked(self):
        commands = [
            "rm -rf build",
            "rm -r -f build",
            "sqlite3 app.db 'DROP TABLE users;'",
            "git push origin main --force",
            "sqlite3 app.db 'TRUNCATE users;'",
            "sqlite3 app.db 'DELETE FROM users;'",
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_hook(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("BLOCKED", result.stderr)

    def test_delete_with_where_is_allowed(self):
        result = self.run_hook("sqlite3 app.db 'DELETE FROM users WHERE id = 7;'")
        self.assertEqual(result.returncode, 0)

    def test_normal_commands_are_not_interfered_with(self):
        commands = [
            "git status",
            "npm test",
            "rm -r build",
            "git push origin main",
            "sqlite3 app.db 'SELECT * FROM users;'",
            "echo 'DELETE FROM users WHERE active = 0;'",
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_hook(command)
                self.assertEqual(result.returncode, 0)

    def test_non_bash_tool_is_ignored(self):
        result = self.run_hook("rm -rf /tmp/example", tool_name="Read")
        self.assertEqual(result.returncode, 0)

    def test_blocked_attempt_is_logged_with_required_fields(self):
        with tempfile.TemporaryDirectory() as home:
            command = "git push --force origin main"
            result = self.run_hook(command, home=home)
            self.assertEqual(result.returncode, 2)
            log = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            record = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
            self.assertTrue(record["timestamp"])
            self.assertEqual(record["command"], command)
            self.assertEqual(record["project_path"], "/tmp/example-project")


if __name__ == "__main__":
    unittest.main(verbosity=2)
