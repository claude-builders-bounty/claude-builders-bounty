import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from destructive_command_guard import blocked_reason


class PolicyTests(unittest.TestCase):
    def test_required_blocks(self):
        blocked = [
            "rm -rf build", "rm -fr build", "rm --recursive --force build",
            "cd /tmp && rm -Rf cache", "git push --force origin main",
            "git push -f", "git push --force-with-lease origin main",
            "psql -c 'DROP TABLE users'", "mysql -e 'TRUNCATE users'",
            "DELETE FROM sessions", "echo ok; DELETE FROM sessions; echo done",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(blocked_reason(command))

    def test_normal_commands_are_allowed(self):
        allowed = [
            "rm -r build", "rm -f file", "git push origin main", "git push --follow-tags",
            "truncate -s 0 app.log", "SELECT * FROM users", "DELETE FROM users WHERE id = 7",
            "echo 'DROP DATABASE is not one of the required patterns'",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(blocked_reason(command))

    def test_where_in_later_statement_does_not_mask_delete(self):
        self.assertIsNotNone(blocked_reason("DELETE FROM a; SELECT * FROM b WHERE id=1"))

    def test_hook_denies_and_logs_current_schema(self):
        script = Path(__file__).with_name("destructive_command_guard.py")
        event = {"tool_name": "Bash", "tool_input": {"command": "rm -rf data"}, "cwd": "/project"}
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [str(script)], input=json.dumps(event), text=True, capture_output=True,
                env={**os.environ, "HOME": home}, check=True,
            )
            output = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            record = json.loads((Path(home) / ".claude/hooks/blocked.log").read_text())
            self.assertEqual(record["attempted_command"], "rm -rf data")
            self.assertEqual(record["project_path"], "/project")


if __name__ == "__main__":
    unittest.main()
