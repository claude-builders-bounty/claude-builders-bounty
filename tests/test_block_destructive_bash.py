import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


def run_hook(command, log_path):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/project",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["CLAUDE_HOOKS_LOG"] = str(log_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashHookTests(unittest.TestCase):
    def test_allows_normal_command_without_logging(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            result = run_hook("git status --short", log_path)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse(log_path.exists())

    def test_blocks_rm_rf_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            result = run_hook("rm -r -f dist", log_path)

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            reason = output["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertIn("rm -r -f", reason)

            entries = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(entries), 1)
            entry = json.loads(entries[0])
            self.assertEqual(entry["command"], "rm -r -f dist")
            self.assertEqual(entry["project_path"], "/tmp/project")

    def test_blocks_force_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("git push origin main --force-with-lease", Path(tmp) / "blocked.log")

            output = json.loads(result.stdout)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("force-pushing", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_allows_delete_from_with_where(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("psql -c \"DELETE FROM users WHERE id = 1\"", Path(tmp) / "blocked.log")

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_blocks_delete_from_without_where(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("psql -c \"DELETE FROM users\"", Path(tmp) / "blocked.log")

            output = json.loads(result.stdout)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("without a WHERE clause", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_blocks_drop_table_and_truncate(self):
        for command in ("psql -c 'DROP TABLE users'", "psql -c 'TRUNCATE TABLE users'"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as tmp:
                result = run_hook(command, Path(tmp) / "blocked.log")

                output = json.loads(result.stdout)
                self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
