import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


def run_hook(command, tool_name="Bash"):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/workspace/example",
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
        log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    return result, log


class DestructiveBashHookTest(unittest.TestCase):
    def assert_blocked(self, command, expected_reason):
        result, log = run_hook(command)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(expected_reason, decision["permissionDecisionReason"])
        log_entry = json.loads(log)
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["project_path"], "/workspace/example")

    def assert_allowed(self, command):
        result, log = run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log, "")

    def test_blocks_recursive_force_remove(self):
        self.assert_blocked("sudo rm -rf ./build", "rm -rf")

    def test_blocks_force_push(self):
        self.assert_blocked("git push origin main --force-with-lease", "force-pushing")

    def test_blocks_drop_table(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")

    def test_blocks_truncate(self):
        self.assert_blocked('mysql -e "TRUNCATE TABLE audit_log"', "TRUNCATE")

    def test_blocks_delete_without_where(self):
        self.assert_blocked('psql -c "DELETE FROM sessions"', "DELETE FROM")

    def test_allows_delete_with_where(self):
        self.assert_allowed('psql -c "DELETE FROM sessions WHERE expires_at < now()"')

    def test_allows_normal_bash_command(self):
        self.assert_allowed("npm test -- --runInBand")

    def test_ignores_non_bash_tool(self):
        result, log = run_hook("rm -rf ./build", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
