import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block-destructive-bash.py"


def run_hook(command, home):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/repo"}
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashHookTests(unittest.TestCase):
    def assert_denied(self, command):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(command, Path(tmp))
            self.assertEqual(result.returncode, 0)
            response = json.loads(result.stdout)
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            log = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            self.assertIn(command.replace("\n", "\\n"), log.read_text())

    def assert_allowed(self, command):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(command, Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(tmp) / ".claude" / "hooks" / "blocked.log").exists())

    def test_all_required_patterns_are_blocked(self):
        for command in [
            "rm -rf build",
            "rm -r -f build",
            "rm -f -R build",
            "rm --recursive --force build",
            "sudo rm -fr /tmp/app",
            "psql -c 'DROP TABLE users'",
            "git push origin main --force",
            "git push --force-with-lease origin main",
            "git push --force-with-lease=refs/heads/main origin main",
            "sqlite3 app.db 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM users'",
        ]:
            with self.subTest(command=command):
                self.assert_denied(command)

    def test_safe_commands_are_allowed(self):
        for command in [
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "npm test",
            "truncate -s 0 file.log",
            "echo 'how to DROP TABLE safely'",
            "echo 'DELETE FROM users'",
            "git push --force-if-includes origin main",
        ]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_non_bash_tool_is_ignored(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
