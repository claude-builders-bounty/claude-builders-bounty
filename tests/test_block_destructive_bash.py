import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "hooks" / "block_destructive_bash.py"


class DestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command, *, tool_name="Bash"):
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/workspace/project",
        }

        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            return result, log_text

    def assert_blocked(self, command, expected_reason):
        result, log_text = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        hook_output = output["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn(expected_reason, hook_output["permissionDecisionReason"])
        self.assertNotEqual(log_text, "")
        log_entry = json.loads(log_text.strip())
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["project_path"], "/workspace/project")
        self.assertIn(expected_reason, log_entry["reason"])

    def assert_allowed(self, command, *, tool_name="Bash"):
        result, log_text = self.run_hook(command, tool_name=tool_name)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_text, "")

    def test_blocks_rm_recursive_force(self):
        self.assert_blocked("npm test && rm -rf dist", "rm recursive force")
        self.assert_blocked("rm -r -f build", "rm recursive force")

    def test_blocks_git_force_push(self):
        self.assert_blocked("git push origin main --force", "git force push")
        self.assert_blocked("git -C repo push -f", "git force push")

    def test_blocks_destructive_sql(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("mysql -e 'TRUNCATE TABLE sessions'", "TRUNCATE")
        self.assert_blocked("psql -c 'DELETE FROM accounts'", "DELETE FROM")

    def test_allows_normal_commands(self):
        self.assert_allowed("git status")
        self.assert_allowed("rm -r build")
        self.assert_allowed("psql -c 'DELETE FROM sessions WHERE id = 1'")

    def test_ignores_non_bash_tools(self):
        self.assert_allowed("rm -rf dist", tool_name="Read")


if __name__ == "__main__":
    unittest.main()
