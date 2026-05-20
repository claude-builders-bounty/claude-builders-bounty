import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[1] / "pre_tool_use.py"


class DestructiveBashGuardTest(unittest.TestCase):
    def run_hook(self, command: str, *, tool_name: str = "Bash"):
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/workspace/project",
        }
        env = {**os.environ, "HOME": home}
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        return result, log_path

    def assert_blocked(self, command: str, expected_rule: str):
        result, log_path = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_rule, output["permissionDecisionReason"])

        log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(log_entry["rule"], expected_rule)
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["project_path"], "/workspace/project")

    def test_blocks_rm_rf_variants(self):
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("rm -fr ./dist", "rm -rf")

    def test_blocks_git_force_push_variants(self):
        self.assert_blocked("git push origin main --force", "git push --force")
        self.assert_blocked("git push -f", "git push --force")
        self.assert_blocked("git push --force-with-lease", "git push --force")

    def test_blocks_required_sql_patterns(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('mysql -e "TRUNCATE audit_log"', "TRUNCATE")
        self.assert_blocked('psql -c "DELETE FROM sessions"', "DELETE FROM without WHERE")

    def test_allows_safe_commands_without_output_or_log(self):
        result, log_path = self.run_hook("rm ./build-output.txt && git status")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(log_path.exists())

    def test_allows_delete_from_with_where(self):
        result, log_path = self.run_hook('psql -c "DELETE FROM sessions WHERE id = 1"')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(log_path.exists())

    def test_ignores_non_bash_tools(self):
        result, log_path = self.run_hook("rm -rf build", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(log_path.exists())


if __name__ == "__main__":
    unittest.main()
