import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_safety.py"


def run_hook(payload, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
        check=False,
    )


def bash_event(command, cwd="/tmp/project"):
    return {
        "session_id": "test-session",
        "cwd": cwd,
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


class PreToolUseSafetyHookTest(unittest.TestCase):
    def test_blocks_rm_rf_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = run_hook(bash_event("rm -rf build"), home)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked dangerous Bash command", result.stderr)
            self.assertIn("rm -rf", result.stderr)

            log_path = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("rm -rf build", log)
            self.assertIn("/tmp/project", log)
            self.assertRegex(log, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_blocks_required_destructive_patterns(self):
        cases = [
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE audit_log",
            "DELETE FROM users",
        ]

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for command in cases:
                with self.subTest(command=command):
                    result = run_hook(bash_event(command), home)

                    self.assertEqual(result.returncode, 2)
                    self.assertIn(command, result.stderr)

    def test_allows_delete_from_when_where_clause_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(
                bash_event("DELETE FROM sessions WHERE expires_at < NOW()"),
                Path(tmp),
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")

    def test_allows_normal_bash_commands_without_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = run_hook(bash_event("npm test"), home)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_ignores_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = run_hook(
                {
                    "cwd": "/tmp/project",
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "tool_input": {"file_path": "README.md"},
                },
                home,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
