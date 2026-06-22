import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_block_destructive_bash.py"


def run_hook(payload, home):
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def bash_payload(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/workspace/project",
    }


class DestructiveBashHookTests(unittest.TestCase):
    def test_allows_normal_bash_command_without_output_or_log(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("git status --short"), home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(home) / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_recursive_force_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("sudo rm -r -f /tmp/build"), home)
            self.assertEqual(result.returncode, 0)
            decision = json.loads(result.stdout)
            hook_output = decision["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm", hook_output["permissionDecisionReason"])

            log_text = (Path(home) / ".claude" / "hooks" / "blocked.log").read_text()
            self.assertIn("/workspace/project", log_text)
            self.assertIn("sudo rm -r -f /tmp/build", log_text)

    def test_blocks_git_force_push(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("git push --force origin main"), home)
            self.assertEqual(result.returncode, 0)
            hook_output = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("force", hook_output["permissionDecisionReason"])

    def test_blocks_sql_destructive_commands(self):
        with tempfile.TemporaryDirectory() as home:
            for command in (
                'psql -c "DROP TABLE users"',
                'psql -c "TRUNCATE sessions"',
                'psql -c "DELETE FROM users"',
            ):
                with self.subTest(command=command):
                    result = run_hook(bash_payload(command), home)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(
                        json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
                        "deny",
                    )

    def test_allows_delete_with_where_clause(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload('psql -c "DELETE FROM users WHERE id = 1"'), home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_ignores_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "tool_input": {"file_path": "rm -rf /"},
                    "cwd": "/workspace/project",
                },
                home,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
