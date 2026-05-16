#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "block-destructive-bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class DetectBlockReasonTests(unittest.TestCase):
    def assert_blocked(self, command, pattern):
        reason = hook.detect_block_reason(command)
        self.assertIsNotNone(reason, command)
        self.assertEqual(reason.pattern, pattern)

    def assert_allowed(self, command):
        self.assertIsNone(hook.detect_block_reason(command), command)

    def test_blocks_rm_rf_variants(self):
        for command in [
            "rm -rf build",
            "rm -fr build",
            "rm -r -f build",
            "rm --recursive --force build",
        ]:
            self.assert_blocked(command, "rm -rf")

    def test_allows_non_recursive_or_non_force_rm(self):
        self.assert_allowed("rm file.txt")
        self.assert_allowed("rm -r build")
        self.assert_allowed("rm -f file.txt")

    def test_blocks_git_force_push(self):
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f", "git push --force")

    def test_sql_dangerous_patterns(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("mysql -e 'TRUNCATE audit_log'", "TRUNCATE")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM users'", "DELETE FROM without WHERE")

    def test_delete_from_with_where_allowed(self):
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'")

    def test_delete_from_without_where_per_statement(self):
        self.assert_blocked(
            "sqlite3 app.db 'DELETE FROM users; SELECT * FROM users WHERE id = 1'",
            "DELETE FROM without WHERE",
        )

    def test_sql_keywords_inside_strings_are_ignored(self):
        self.assert_allowed("echo 'DROP TABLE users'")
        self.assert_allowed("printf 'DELETE FROM users'")


class HookProcessTests(unittest.TestCase):
    def run_payload(self, payload, home):
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_allow_normal_bash_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_payload(
                {"tool_name": "Bash", "tool_input": {"command": "npm test"}, "cwd": "/repo"},
                Path(tmp),
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(tmp) / ".claude/hooks/blocked.log").exists())

    def test_block_writes_decision_and_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_payload(
                {"tool_name": "Bash", "tool_input": {"command": "rm -rf build"}, "cwd": "/repo"},
                Path(tmp),
            )
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_path = Path(tmp) / ".claude/hooks/blocked.log"
            log_entry = json.loads(log_path.read_text().strip())
            self.assertEqual(log_entry["command"], "rm -rf build")
            self.assertEqual(log_entry["project_path"], "/repo")
            self.assertEqual(log_entry["pattern"], "rm -rf")


if __name__ == "__main__":
    unittest.main()
