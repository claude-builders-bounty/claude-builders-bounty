import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive_command_guard.py"


def run_hook(command, home, cwd="/tmp/project", tool_name="Bash"):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": cwd,
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


class DestructiveCommandGuardTests(unittest.TestCase):
    def test_all_required_patterns_are_blocked_and_logged(self):
        blocked = [
            "rm -rf build",
            "rm -fr ./dist",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "sqlite3 db.sqlite 'TRUNCATE TABLE events'",
            "psql -c 'DELETE FROM users'",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for command in blocked:
                result = run_hook(command, home)
                self.assertEqual(result.returncode, 0)
                self.assertIn('"permissionDecision": "deny"', result.stdout)
                self.assertIn("Destructive command blocked", result.stdout)

            log_path = home / ".claude" / "hooks" / "blocked.log"
            entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(entries), len(blocked))
            self.assertTrue(all("timestamp" in entry for entry in entries))
            self.assertTrue(all(entry["project_path"] == "/tmp/project" for entry in entries))
            self.assertEqual(entries[0]["attempted_command"], "rm -rf build")

    def test_normal_commands_are_not_blocked(self):
        allowed = [
            "ls -la",
            "git status",
            "git push origin main",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "python -m pytest",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for command in allowed:
                result = run_hook(command, home)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
            self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_non_bash_tools_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("rm -rf build", Path(tmp), tool_name="Read")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
