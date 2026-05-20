import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).parents[1] / "hooks" / "pre-tool-use" / "destructive-bash-guard.py"
INSTALLER = Path(__file__).parents[1] / "hooks" / "pre-tool-use" / "install.py"


def run_hook(tmp_path, command, tool_name="Bash", hook_event_name="PreToolUse"):
    payload = {
        "session_id": "test-session",
        "transcript_path": str(tmp_path / "transcript.jsonl"),
        "cwd": str(tmp_path / "project"),
        "hook_event_name": hook_event_name,
        "tool_name": tool_name,
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def denied_output(result):
    return json.loads(result.stdout)["hookSpecificOutput"]


class DestructiveBashGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def assert_denied(self, result, expected_reason):
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        hook_output = denied_output(result)
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn(expected_reason, hook_output["permissionDecisionReason"])

    def test_allows_normal_bash_command(self):
        result = run_hook(self.tmp_path, "git status --short")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse((self.tmp_path / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_rf_and_logs_attempt(self):
        result = run_hook(self.tmp_path, "rm -rf build")

        self.assert_denied(result, "rm -rf")
        log_path = self.tmp_path / ".claude" / "hooks" / "blocked.log"
        log_record = json.loads(log_path.read_text().strip())
        self.assertEqual(log_record["attempted_command"], "rm -rf build")
        self.assertEqual(log_record["project_path"], str(self.tmp_path / "project"))
        self.assertIn("timestamp", log_record)

    def test_blocks_sql_patterns(self):
        cases = [
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("mysql -e 'TRUNCATE sessions'", "TRUNCATE"),
            ("psql -c 'DELETE FROM accounts'", "DELETE FROM without WHERE"),
        ]

        for command, expected_reason in cases:
            with self.subTest(command=command):
                self.assert_denied(run_hook(self.tmp_path, command), expected_reason)

    def test_allows_delete_with_where(self):
        result = run_hook(self.tmp_path, "psql -c 'DELETE FROM accounts WHERE id = 1'")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocks_forced_git_push(self):
        self.assert_denied(run_hook(self.tmp_path, "git push --force origin main"), "git push --force")
        self.assert_denied(run_hook(self.tmp_path, "git push -f origin main"), "git push --force")

    def test_ignores_non_bash_tools(self):
        result = run_hook(self.tmp_path, "rm -rf build", tool_name="Read")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse((self.tmp_path / ".claude" / "hooks" / "blocked.log").exists())

    def test_installer_copies_hook_and_updates_settings(self):
        env = os.environ.copy()
        env["HOME"] = str(self.tmp_path)

        result = subprocess.run(
            [sys.executable, str(INSTALLER)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        installed_hook = self.tmp_path / ".claude" / "hooks" / "destructive-bash-guard.py"
        settings_path = self.tmp_path / ".claude" / "settings.json"
        self.assertTrue(installed_hook.exists())
        self.assertTrue(os.access(installed_hook, os.X_OK))

        settings = json.loads(settings_path.read_text())
        pre_tool_use = settings["hooks"]["PreToolUse"]
        self.assertEqual(pre_tool_use[0]["matcher"], "Bash")
        self.assertEqual(pre_tool_use[0]["hooks"][0]["command"], str(installed_hook))


if __name__ == "__main__":
    unittest.main()
