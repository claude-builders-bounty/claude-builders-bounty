#!/usr/bin/env python3

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "pre-tool-use.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CheckCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hook = load_hook_module()

    def test_blocks_rm_rf(self):
        self.assertEqual(
            self.hook.check_command("rm -rf /tmp/build"),
            "Recursive force delete (rm -rf)",
        )

    def test_blocks_rm_fr(self):
        self.assertEqual(
            self.hook.check_command("rm -fr /tmp/build"),
            "Recursive force delete (rm -rf)",
        )

    def test_blocks_rm_r_f_separate_flags(self):
        self.assertEqual(
            self.hook.check_command("rm -r -f /tmp/build"),
            "Recursive force delete (rm -rf)",
        )

    def test_allows_rm_f_only(self):
        self.assertIsNone(self.hook.check_command("rm -f README.md"))

    def test_blocks_drop_table(self):
        self.assertEqual(
            self.hook.check_command("sqlite3 db.sqlite 'DROP TABLE users'"),
            "SQL DROP TABLE",
        )

    def test_blocks_git_push_force(self):
        self.assertEqual(
            self.hook.check_command("git push --force origin main"),
            "Git force push (git push --force)",
        )

    def test_blocks_git_push_f(self):
        self.assertEqual(
            self.hook.check_command("git push -f origin main"),
            "Git force push (git push -f)",
        )

    def test_blocks_truncate(self):
        self.assertEqual(
            self.hook.check_command("psql -c 'TRUNCATE sessions'"),
            "SQL TRUNCATE",
        )

    def test_blocks_delete_from_without_where(self):
        self.assertEqual(
            self.hook.check_command("sqlite3 db.sqlite 'DELETE FROM users'"),
            "SQL DELETE FROM without WHERE clause",
        )

    def test_allows_delete_from_with_where(self):
        self.assertIsNone(
            self.hook.check_command("sqlite3 db.sqlite 'DELETE FROM users WHERE id = 1'")
        )

    def test_allows_git_push_force_with_lease(self):
        self.assertIsNone(
            self.hook.check_command("git push --force-with-lease origin main")
        )

    def test_blocks_rm_recursive_force_long_flags(self):
        self.assertEqual(
            self.hook.check_command("rm --recursive --force /var/log"),
            "Recursive force delete (rm -rf)",
        )

    def test_blocks_delete_from_case_insensitive(self):
        self.assertEqual(
            self.hook.check_command("psql -c 'delete from sessions'"),
            "SQL DELETE FROM without WHERE clause",
        )

    def test_blocks_git_push_force_mixed_case(self):
        self.assertEqual(
            self.hook.check_command("GIT PUSH --FORCE origin main"),
            "Git force push (git push --force)",
        )

    def test_parametrized_blocked_commands(self):
        blocked = (
            ("rm -rf /", "Recursive force delete (rm -rf)"),
            ("rm -fr build/", "Recursive force delete (rm -rf)"),
            ("rm -r -f node_modules", "Recursive force delete (rm -rf)"),
            ("DROP TABLE users", "SQL DROP TABLE"),
            ("drop table accounts", "SQL DROP TABLE"),
            ("TRUNCATE sessions", "SQL TRUNCATE"),
            ("truncate logs", "SQL TRUNCATE"),
            ("git push --force origin main", "Git force push (git push --force)"),
            ("git push -f origin main", "Git force push (git push -f)"),
            ("DELETE FROM users", "SQL DELETE FROM without WHERE clause"),
        )
        for command, reason in blocked:
            with self.subTest(command=command):
                self.assertEqual(self.hook.check_command(command), reason)

    def test_parametrized_allowed_commands(self):
        allowed = (
            "ls -la",
            "git status",
            "npm test",
            "rm README.md",
            "rm -f README.md",
            "rm -r build",
            "git push origin main",
            "git push --force-with-lease origin main",
            "DELETE FROM users WHERE id = 1",
            "echo 'DELETE FROM backup' > notes.txt",
            "cat notes.txt | grep DELETE FROM",
        )
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(self.hook.check_command(command))


class HookIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_dir = Path(self.temp_dir.name) / ".claude" / "hooks"
        self.log_dir.mkdir(parents=True)
        self.log_file = self.log_dir / "blocked.log"
        self.env = os.environ.copy()
        self.env["HOME"] = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook(self, payload: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )

    def test_blocks_and_logs_destructive_command(self):
        result = self.run_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
                "cwd": "/workspace/demo",
            }
        )

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(
            output["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )
        self.assertIn("rm -rf", output["hookSpecificOutput"]["permissionDecisionReason"])

        log_contents = self.log_file.read_text(encoding="utf-8")
        self.assertIn("rm -rf /", log_contents)
        self.assertIn("/workspace/demo", log_contents)

    def test_allows_safe_command(self):
        result = self.run_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
                "cwd": "/workspace/demo",
            }
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertFalse(self.log_file.exists())

    def test_ignores_non_bash_tools(self):
        result = self.run_hook(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "README.md", "content": "rm -rf /"},
                "cwd": "/workspace/demo",
            }
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertFalse(self.log_file.exists())

    def test_malformed_json_exits_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not-json",
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertFalse(self.log_file.exists())

    def test_empty_stdin_exits_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="",
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertFalse(self.log_file.exists())


if __name__ == "__main__":
    unittest.main()
