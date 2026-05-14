import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "destructive_command_guard.py"


def run_hook(command: str, home: str) -> dict:
    payload = {
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/workspace/project",
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["HOME"] = home
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=True,
    )
    return json.loads(result.stdout)


def run_non_bash_hook(home: str) -> dict:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": "README.md"},
    }
    env = os.environ.copy()
    env["HOME"] = home
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=True,
    )
    return json.loads(result.stdout)


class DestructiveCommandGuardTest(unittest.TestCase):
    def assert_denied(self, command: str) -> None:
        with tempfile.TemporaryDirectory() as home:
            output = run_hook(command, home)
            decision = output["hookSpecificOutput"]["permissionDecision"]
            self.assertEqual(decision, "deny")

    def test_blocks_required_destructive_patterns(self) -> None:
        self.assert_denied("rm -rf node_modules")
        self.assert_denied("rm -fr /tmp/build")
        self.assert_denied("rm -r -f .cache")
        self.assert_denied("rm --recursive --force build")
        self.assert_denied("echo ok && rm -rf dist")
        self.assert_denied("psql -c 'DROP TABLE users'")
        self.assert_denied("psql -c 'drop table users'")
        self.assert_denied("git push origin main --force")
        self.assert_denied("git push --force-with-lease origin main")
        self.assert_denied("git push -f origin main")
        self.assert_denied("psql -c 'TRUNCATE audit_log'")
        self.assert_denied("psql -c 'DELETE FROM users;'")

    def test_allows_normal_commands_and_scoped_delete(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(run_hook("ls -la", home), {"continue": True})
            self.assertEqual(run_hook("rm -r old-build", home), {"continue": True})
            self.assertEqual(run_hook("rm -f one-file.tmp", home), {"continue": True})
            self.assertEqual(run_hook("git status --short", home), {"continue": True})
            self.assertEqual(run_non_bash_hook(home), {"continue": True})
            self.assertEqual(
                run_hook("psql -c 'DELETE FROM sessions WHERE expires_at < now();'", home),
                {"continue": True},
            )

    def test_logs_blocked_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            run_hook("rm -rf dist", home=home)
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["command"], "rm -rf dist")
            self.assertEqual(entry["project_path"], "/workspace/project")
            self.assertIn("recursive forced removal", entry["reason"])


if __name__ == "__main__":
    unittest.main()
