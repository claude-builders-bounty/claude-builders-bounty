import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "destructive-command-guard.py"


def run_hook(command: str, home: Path, cwd: str = "/tmp/example-project"):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    }
    env = os.environ.copy()
    env["HOME"] = str(home)

    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    output = json.loads(proc.stdout) if proc.stdout.strip() else None
    return proc, output


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def assertBlocked(self, command: str):
        proc, output = run_hook(command, self.home)
        self.assertEqual(proc.returncode, 0)
        self.assertIsNotNone(output)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")

    def assertAllowed(self, command: str):
        proc, output = run_hook(command, self.home)
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(output)

    def test_required_block_patterns(self):
        for command in [
            "rm -rf build/",
            "rm -fr ./cache",
            "psql -c 'DROP TABLE users;'",
            "git push origin main --force",
            "TRUNCATE TABLE sessions;",
            "DELETE FROM users;",
        ]:
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_normal_commands_are_allowed(self):
        for command in [
            "rm build.log",
            "git push origin main",
            "SELECT * FROM users;",
            "DELETE FROM users WHERE id = 42;",
            "npm test",
            "python -m pytest",
        ]:
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_block_is_logged_with_required_fields(self):
        attempted = "rm -rf /tmp/example"
        project = "/work/acme"
        proc, _ = run_hook(attempted, self.home, cwd=project)
        self.assertEqual(proc.returncode, 0)

        log_path = self.home / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_path.exists())

        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["command"], attempted)
        self.assertEqual(entry["project_path"], project)


if __name__ == "__main__":
    unittest.main()
