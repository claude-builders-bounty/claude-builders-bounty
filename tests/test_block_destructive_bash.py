import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


class BlockDestructiveBashTest(unittest.TestCase):
    def run_hook(self, command):
        tempdir = tempfile.TemporaryDirectory()
        home = Path(tempdir.name)
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": str(ROOT),
            "tool_input": {"command": command},
        }
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.addCleanup(tempdir.cleanup)
        return proc, home

    def assert_blocked(self, command, expected_reason):
        proc, home = self.run_hook(command)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        response = json.loads(proc.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_reason, output["permissionDecisionReason"])

        log_path = home / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_path.exists())
        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(entry["attempted_command"], command)
        self.assertEqual(entry["project_path"], str(ROOT))
        self.assertIn(expected_reason, entry["reasons"])

    def assert_allowed(self, command):
        proc, home = self.run_hook(command)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_recursive_force_rm_variants(self):
        self.assert_blocked("rm -rf /tmp/build", "rm with recursive and force flags")
        self.assert_blocked("sudo rm -r -f /tmp/build", "rm with recursive and force flags")
        self.assert_blocked("rm --recursive --force /tmp/build", "rm with recursive and force flags")

    def test_blocks_force_push_variants(self):
        self.assert_blocked("git push --force origin main", "git push with force flag")
        self.assert_blocked("git -C repo push -f origin main", "git push with force flag")
        self.assert_blocked("bash -c 'git push --force-with-lease'", "git push with force flag")

    def test_blocks_dangerous_sql_in_sql_contexts(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE statement")
        self.assert_blocked("mysql -e 'TRUNCATE users'", "TRUNCATE statement")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM users'", "DELETE FROM without WHERE clause")
        self.assert_blocked("DELETE FROM users", "DELETE FROM without WHERE clause")

    def test_allows_safe_commands(self):
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm build.log")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'")
        self.assert_allowed("echo 'DROP TABLE users'")


if __name__ == "__main__":
    unittest.main()
