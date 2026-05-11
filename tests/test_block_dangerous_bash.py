import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / ".claude" / "hooks" / "block-dangerous-bash.py"


class BlockDangerousBashTests(unittest.TestCase):
    def run_hook(self, command: str, project_path: str = "/tmp/project"):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": project_path,
        }

        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            env["USERPROFILE"] = temp_home

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            log_path = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            log_lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []

        return result, log_lines

    def assert_blocked(self, command: str, expected_reason: str):
        result, log_lines = self.run_hook(command)

        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        decision = response["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(expected_reason, decision["permissionDecisionReason"])

        self.assertEqual(len(log_lines), 1)
        log_entry = json.loads(log_lines[0])
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/project")
        self.assertEqual(log_entry["reason"], expected_reason)
        self.assertIn("timestamp", log_entry)

    def test_all_required_dangerous_patterns_are_blocked(self):
        cases = [
            ("rm -rf build", "rm -rf"),
            ('psql -c "DROP TABLE users"', "DROP TABLE"),
            ("git push origin main --force", "git push --force"),
            ('psql -c "TRUNCATE events"', "TRUNCATE"),
            ('psql -c "DELETE FROM users"', "DELETE FROM without WHERE"),
        ]

        for command, expected_reason in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, expected_reason)

    def test_delete_from_with_where_is_allowed(self):
        result, log_lines = self.run_hook('psql -c "DELETE FROM users WHERE id = 1"')

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_lines, [])

    def test_normal_bash_command_is_allowed(self):
        result, log_lines = self.run_hook("git status --short")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_lines, [])


if __name__ == "__main__":
    unittest.main()
