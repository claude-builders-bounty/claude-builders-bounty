import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


class DestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command: str) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/example-project",
            "tool_input": {"command": command},
        }
        env = os.environ.copy()
        env["CLAUDE_BLOCKED_LOG"] = str(Path(tempfile.gettempdir()) / "claude-blocked-test.log")
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def assert_blocked(self, command: str, expected_text: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)
        hook_output = output["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn(expected_text, hook_output["permissionDecisionReason"])

    def assert_allowed(self, command: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "recursive force")
        self.assert_blocked("rm -fr ./dist", "recursive force")
        self.assert_blocked("rm -r -f ./dist", "recursive force")
        self.assert_blocked("rm --recursive --force ./dist", "recursive force")
        self.assert_blocked("sudo rm -Rf /tmp/app", "recursive force")

    def test_blocks_sql_destructive_patterns(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('mysql -e "TRUNCATE TABLE sessions"', "TRUNCATE")
        self.assert_blocked('psql -c "DELETE FROM users"', "DELETE FROM without a WHERE")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "force")
        self.assert_blocked("git push -f origin main", "force")

    def test_allows_safe_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("rm -r build")
        self.assert_allowed("git push origin main")
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')


if __name__ == "__main__":
    unittest.main()
