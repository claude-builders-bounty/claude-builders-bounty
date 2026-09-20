import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("pre_tool_use_guard.py")


def run(command: str, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({"cwd": "/tmp/project", "tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class GuardTests(unittest.TestCase):
    def test_safe_commands_are_allowed(self):
        for command in ("ls -la", "git push origin main", "DELETE FROM users WHERE id = 1"):
            self.assertEqual(run(command).returncode, 0)

    def test_dangerous_commands_are_denied(self):
        for command in (
            "rm -rf ./build",
            "rm -r -f ./build",
            "rm --recursive --force ./build",
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE TABLE users",
            "DELETE FROM users",
        ):
            result = run(command)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked dangerous command", result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Blocked dangerous command", payload["systemMessage"])

    def test_denied_attempt_logs_timestamp_command_and_project(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = run("TRUNCATE TABLE users", env=env)
            self.assertEqual(result.returncode, 2)
            log = Path(home) / ".claude" / "hooks" / "blocked.log"
            line = log.read_text(encoding="utf-8").strip()
            timestamp, project, command = line.split("\t", 2)
            self.assertTrue(timestamp.endswith("+00:00"))
            self.assertEqual(project, "/tmp/project")
            self.assertEqual(command, "TRUNCATE TABLE users")


if __name__ == "__main__":
    unittest.main()
