import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_block_destructive_bash.py"


class DestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command, *, tool_name="Bash"):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ)
            env["HOME"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
        return result, log_lines

    def assert_blocked(self, command, pattern):
        result, log_lines = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(pattern, output["permissionDecisionReason"])
        self.assertEqual(len(log_lines), 1)
        log_entry = json.loads(log_lines[0])
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/example-project")
        self.assertEqual(log_entry["pattern"], pattern)

    def assert_allowed(self, command, *, tool_name="Bash"):
        result, log_lines = self.run_hook(command, tool_name=tool_name)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_lines, [])

    def test_blocks_rm_rf_variants(self):
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("sudo rm -fr /tmp/output", "rm -rf")
        self.assert_blocked("rm -r -f dist", "rm -rf")

    def test_blocks_git_force_push(self):
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")
        self.assert_blocked("git push --force-with-lease origin main", "git push --force")

    def test_blocks_destructive_sql(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('mysql -e "TRUNCATE audit_log"', "TRUNCATE")
        self.assert_blocked('sqlite3 app.db "DELETE FROM sessions"', "DELETE FROM without WHERE")

    def test_allows_delete_with_where_and_normal_commands(self):
        self.assert_allowed('sqlite3 app.db "DELETE FROM sessions WHERE id = 1"')
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm build/output.txt")
        self.assert_allowed("npm test")

    def test_allows_documenting_or_searching_destructive_sql_text(self):
        self.assert_allowed('echo "DROP TABLE users"')
        self.assert_allowed('printf "TRUNCATE audit_log"')
        self.assert_allowed('rg "DELETE FROM sessions" docs/')

    def test_ignores_non_bash_tools(self):
        self.assert_allowed("rm -rf build", tool_name="Read")


if __name__ == "__main__":
    unittest.main()
