from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "destructive_command_guard.py"

spec = importlib.util.spec_from_file_location("guard", HOOK)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class PatternTests(unittest.TestCase):
    def test_required_destructive_patterns_are_blocked(self):
        cases = {
            "rm -rf build/": "rm -rf",
            "rm -fr build/": "rm -rf",
            "psql -c 'DROP TABLE users'": "DROP TABLE",
            "git push origin main --force": "git push --force",
            "sqlite3 app.db 'TRUNCATE TABLE events'": "TRUNCATE",
            "psql -c 'DELETE FROM users;'": "DELETE FROM without WHERE",
        }
        for command, reason in cases.items():
            with self.subTest(command=command):
                self.assertIn(reason, guard.block_reason(command))

    def test_delete_with_where_is_allowed(self):
        self.assertIsNone(
            guard.block_reason("psql -c 'DELETE FROM users WHERE id = 42;'")
        )

    def test_normal_commands_are_allowed(self):
        allowed = [
            "rm build.log",
            "git push origin main",
            "python -m pytest",
            "SELECT * FROM users",
            "DELETE FROM users WHERE inactive = true",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.block_reason(command))


class HookProcessTests(unittest.TestCase):
    def run_hook(self, command: str, home: Path):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/workspace/example",
        }
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_blocked_command_returns_claude_pretooluse_denial_and_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_hook("rm -rf /tmp/build", home)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("rm -rf", output["permissionDecisionReason"])

            log = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            content = log.read_text(encoding="utf-8")
            self.assertIn("project=/workspace/example", content)
            self.assertIn("command=rm -rf /tmp/build", content)

    def test_safe_command_is_silent_and_not_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_hook("git status", home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
