import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive_bash_guard.py"
INSTALLER = ROOT / "install.sh"


class DestructiveBashGuardTests(unittest.TestCase):
    def run_hook(self, command, tool_name="Bash", cwd="/tmp/project"):
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": tool_name,
                "tool_input": {"command": command},
                "cwd": cwd,
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
            log_rows = []
            if log_path.exists():
                with log_path.open(encoding="utf-8") as log_file:
                    log_rows = list(csv.reader(log_file))
            return result, log_rows

    def assert_blocked(self, command, reason_fragment):
        result, log_rows = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(reason_fragment, decision["permissionDecisionReason"])
        self.assertEqual(len(log_rows), 1)
        self.assertEqual(log_rows[0][1], "/tmp/project")
        self.assertIn(reason_fragment, log_rows[0][2])
        self.assertEqual(log_rows[0][3], command)

    def assert_allowed(self, command, tool_name="Bash"):
        result, log_rows = self.run_hook(command, tool_name=tool_name)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(log_rows, [])

    def test_blocks_rm_rf_variations(self):
        self.assert_blocked("rm -rf build", "rm was invoked")
        self.assert_blocked("rm -fr ./dist", "rm was invoked")
        self.assert_blocked("find . -name cache -print && rm --recursive --force cache", "rm was invoked")

    def test_blocks_git_force_push_variations(self):
        self.assert_blocked("git push --force origin main", "git push")
        self.assert_blocked("git push origin main -f", "git push")
        self.assert_blocked("git push --force-with-lease=refs/heads/main", "git push")

    def test_blocks_destructive_sql(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked("mysql -e 'truncate sessions'", "TRUNCATE")
        self.assert_blocked('sqlite3 app.db "DELETE FROM users"', "DELETE FROM")

    def test_allows_delete_from_with_where(self):
        self.assert_allowed('sqlite3 app.db "DELETE FROM users WHERE id = 1"')

    def test_allows_safe_commands_and_false_positive_edges(self):
        self.assert_allowed("rm -r build")
        self.assert_allowed("rm -f one-file.txt")
        self.assert_allowed("git push origin main")
        self.assert_allowed('echo "DROP TABLE users"')
        self.assert_allowed("grep -R 'DELETE FROM' docs/")
        self.assert_allowed("npm test && git status")

    def test_ignores_non_bash_tools(self):
        self.assert_allowed("rm -rf build", tool_name="Read")


class InstallerTests(unittest.TestCase):
    def test_installer_copies_hook_and_configures_pre_tool_use(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [str(INSTALLER)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
                cwd=ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            installed_hook = Path(home) / ".claude" / "hooks" / "destructive_bash_guard.py"
            settings_path = Path(home) / ".claude" / "settings.json"
            self.assertTrue(installed_hook.exists())
            self.assertTrue(os.access(installed_hook, os.X_OK))

            with settings_path.open(encoding="utf-8") as settings_file:
                settings = json.load(settings_file)

            self.assertEqual(
                settings["hooks"]["PreToolUse"],
                [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": str(installed_hook),
                            }
                        ],
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
