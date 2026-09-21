import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "destructive_command_guard.py"
sys.path.insert(0, str(ROOT))

from destructive_command_guard import blocked_reason  # noqa: E402


class PatternTests(unittest.TestCase):
    def test_required_destructive_patterns(self):
        cases = [
            "rm -rf build/",
            "rm -fr /tmp/test",
            "psql -c 'DROP TABLE users'",
            "git push origin main --force",
            "git push -f origin main",
            "mysql -e 'TRUNCATE TABLE sessions'",
            "psql -c 'DELETE FROM users'",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNotNone(blocked_reason(command))

    def test_delete_with_where_is_allowed(self):
        self.assertIsNone(blocked_reason("psql -c 'DELETE FROM users WHERE id = 42'"))

    def test_normal_commands_are_allowed(self):
        cases = [
            "rm -r build/",
            "git push origin main",
            "git status",
            "npm test",
            "python3 -m pytest",
            "echo 'TRUNCATED output'",
            "SELECT * FROM users",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNone(blocked_reason(command))


class HookProtocolTests(unittest.TestCase):
    def run_hook(self, command: str, home: Path):
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
        env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_block_returns_structured_deny_and_logs(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            result = self.run_hook("rm -rf build/", home)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            specific = payload["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], "PreToolUse")
            self.assertEqual(specific["permissionDecision"], "deny")
            self.assertIn("rm -rf", specific["permissionDecisionReason"])

            log = home / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log.read_text().strip())
            self.assertEqual(record["command"], "rm -rf build/")
            self.assertEqual(record["project_path"], "/tmp/example-project")
            self.assertIn("timestamp", record)

    def test_safe_command_is_silent(self):
        with tempfile.TemporaryDirectory() as td:
            result = self.run_hook("git status", Path(td))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
