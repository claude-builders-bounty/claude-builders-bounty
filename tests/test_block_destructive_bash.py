#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "hooks" / "block_destructive_bash.py"


class BlockDestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command, tool_name="Bash"):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            env["CLAUDE_PROJECT_DIR"] = "/tmp/project"
            payload = {"tool_name": tool_name, "tool_input": {"command": command}}
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            log_file = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_text = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
            return result.stdout.strip(), log_text

    def assert_blocked(self, command, expected_reason):
        stdout, log_text = self.run_hook(command)
        self.assertTrue(stdout)
        payload = json.loads(stdout)
        hook_output = payload["hookSpecificOutput"]
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn(expected_reason, hook_output["permissionDecisionReason"])
        self.assertIn(command, log_text)
        self.assertIn("/tmp/project", log_text)

    def test_blocks_required_patterns(self):
        cases = [
            ("rm -rf /tmp/build", "rm -rf"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push --force origin main", "git push --force"),
            ("mysql -e 'TRUNCATE audit_log'", "TRUNCATE"),
            ("psql -c 'DELETE FROM users'", "DELETE FROM without WHERE"),
        ]

        for command, reason in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, reason)

    def test_allows_normal_bash_commands(self):
        stdout, log_text = self.run_hook("git status && npm test")
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")

    def test_allows_delete_with_where_clause(self):
        stdout, log_text = self.run_hook("psql -c 'DELETE FROM sessions WHERE expired = true'")
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")

    def test_ignores_non_bash_tools(self):
        stdout, log_text = self.run_hook("rm -rf /tmp/build", tool_name="Read")
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")

    def test_install_writes_claude_settings(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK), "--install"],
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            settings_path = Path(home) / ".claude" / "settings.json"
            self.assertTrue(settings_path.exists())
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            entry = settings["hooks"]["PreToolUse"][0]
            self.assertEqual(entry["matcher"], "Bash")
            self.assertEqual(entry["hooks"][0]["type"], "command")
            self.assertIn("block_destructive_bash.py", entry["hooks"][0]["command"])
            self.assertIn(str(settings_path), result.stdout)


if __name__ == "__main__":
    unittest.main()
