import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "hooks" / "destructive-command-guard" / "pre_tool_use_destructive_guard.py"


class DestructiveCommandGuardTest(unittest.TestCase):
    def run_hook(self, command, tool_name="Bash"):
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "tool_name": tool_name,
                "tool_input": {"command": command},
                "cwd": "/tmp/example-project",
            }
            env = os.environ.copy()
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
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            return result, log_text

    def assert_blocked(self, command, expected):
        result, log_text = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected, output["permissionDecisionReason"])
        log_entry = json.loads(log_text)
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/example-project")
        self.assertIn(expected.split()[0], log_entry["reason"])

    def assert_allowed(self, command, tool_name="Bash"):
        result, log_text = self.run_hook(command, tool_name=tool_name)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_text, "")

    def test_blocks_rm_rf_variants(self):
        self.assert_blocked("rm -rf build", "rm")
        self.assert_blocked("rm -fr ./dist", "rm")
        self.assert_blocked("rm -r --force ./cache", "rm")

    def test_allows_non_force_rm(self):
        self.assert_allowed("rm old-file.txt")
        self.assert_allowed("rm -r empty-directory")

    def test_blocks_forced_git_push(self):
        self.assert_blocked("git push --force origin main", "Forced git pushes")
        self.assert_blocked("git -C repo push -f origin main", "Forced git pushes")
        self.assert_blocked("git push origin +main:main", "Forced git pushes")

    def test_blocks_destructive_sql(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("mysql -e 'TRUNCATE TABLE sessions'", "TRUNCATE")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM accounts;'", "DELETE FROM")

    def test_allows_safe_sql_and_text_search(self):
        self.assert_allowed("psql -c 'DELETE FROM accounts WHERE id = 1'")
        self.assert_allowed("rg 'DROP TABLE' docs/")
        self.assert_allowed("echo 'DELETE FROM users'")

    def test_checks_each_shell_segment_for_sql(self):
        self.assert_blocked(
            "echo 'migration starting'; psql -c 'DROP TABLE users'",
            "DROP TABLE",
        )
        self.assert_blocked(
            "printf '%s\n' safe | mysql -e 'DELETE FROM accounts'",
            "DELETE FROM",
        )
        self.assert_blocked("echo 'DROP TABLE users' | psql", "DROP TABLE")

    def test_inspects_nested_shell_command(self):
        self.assert_blocked("bash -c 'rm -rf /tmp/example'", "rm")

    def test_ignores_non_bash_tools_and_invalid_json(self):
        self.assert_allowed("rm -rf build", tool_name="Read")
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="{not-json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_installer_is_idempotent(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            installer = REPO_ROOT / "hooks" / "destructive-command-guard" / "install.sh"

            for _ in range(2):
                subprocess.run(
                    ["bash", str(installer)],
                    text=True,
                    capture_output=True,
                    env=env,
                    check=True,
                )

            settings_path = Path(home) / ".claude" / "settings.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            entries = settings["hooks"]["PreToolUse"]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["matcher"], "Bash")


if __name__ == "__main__":
    unittest.main()
