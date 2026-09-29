import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from destructive_guard import reason


class GuardTests(unittest.TestCase):
    def test_destructive_patterns(self):
        commands = [
            "rm -rf /tmp/example", "rm -f -R /tmp/example", "/bin/rm --recursive --force x",
            "sudo rm -fr x", "env X=1 rm -rf x", "true; rm -rf x", "true\nrm -rf x",
            "git push --force origin main", "git push -f", "git push --force-with-lease=main",
            "git push origin +main", "git -C '/project with spaces' push -f", "bash -lc 'rm -rf x'", "eval 'rm -rf x'",
            'echo "$(rm -rf x)"', "echo `rm -rf x`", "DROP TABLE users", "TRUNCATE users",
            'sqlite3 db "DELETE FROM users"', 'psql -c "DELETE FROM users; DELETE FROM logs WHERE id=1"',
            'psql -c "DELETE FROM users -- WHERE id=1"', 'psql -c "DELETE FROM users /* WHERE id=1 */"',
            "psql -c \"DELETE FROM users RETURNING 'WHERE'\"",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(reason(command))

    def test_safe_commands(self):
        for command in ["ls -la", "git status", "git push origin main", "rm file.txt", "rm -r example",
                        "rm -- -rf", "echo 'rm -rf x'", "printf '%s' 'DROP TABLE users'", "# rm -rf x\nls",
                        'sqlite3 db "DELETE FROM users WHERE id=1"', "bash -c 'echo hello'", "git branch -f push"]:
            with self.subTest(command=command):
                self.assertIsNone(reason(command))

    def test_protocol_logging_and_installer(self):
        here = Path(__file__).parent
        with tempfile.TemporaryDirectory(prefix="hook-check-") as home:
            env = {**os.environ, "HOME": home}
            data = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf x"}, "cwd": "/project with spaces"}
            result = subprocess.run([sys.executable, str(here / "destructive_guard.py")], input=json.dumps(data), text=True, capture_output=True, env=env)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
            record = json.loads((Path(home) / ".claude/hooks/blocked.log").read_text())
            self.assertEqual(record["project_path"], data["cwd"])
            self.assertEqual(record["command"], "rm -rf x")
            settings = Path(home) / ".claude/settings.json"
            settings.write_text(json.dumps({"model": "existing", "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": []}]}}))
            for _ in range(2):
                subprocess.run([sys.executable, str(here / "install.py")], env=env, check=True, capture_output=True)
            installed = json.loads(settings.read_text())
            self.assertEqual(installed["model"], "existing")
            self.assertEqual(len(installed["hooks"]["PreToolUse"]), 2)
            data["tool_input"]["command"] = "git status"
            result = subprocess.run([sys.executable, str(here / "destructive_guard.py")], input=json.dumps(data), text=True, capture_output=True, env=env)
            self.assertEqual((result.returncode, result.stdout), (0, ""))
            malformed = subprocess.run([sys.executable, str(here / "destructive_guard.py")], input="{", text=True, capture_output=True, env=env)
            self.assertEqual(malformed.returncode, 2)
            self.assertEqual(len((Path(home) / ".claude/hooks/blocked.log").read_text().splitlines()), 2)

    def test_logging_failure_still_denies(self):
        here = Path(__file__).parent
        with tempfile.TemporaryDirectory(prefix="hook-log-failure-") as home:
            directory = Path(home) / ".claude/hooks"
            directory.mkdir(parents=True)
            target = Path(home) / "unrelated.txt"
            target.write_text("unchanged")
            (directory / "blocked.log").symlink_to(target)
            data = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf x"}}
            result = subprocess.run([sys.executable, str(here / "destructive_guard.py")], input=json.dumps(data), text=True, capture_output=True, env={**os.environ, "HOME": home})
            self.assertEqual(result.returncode, 2)
            self.assertIn("Audit logging failed", json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertEqual(target.read_text(), "unchanged")


if __name__ == "__main__":
    unittest.main()
