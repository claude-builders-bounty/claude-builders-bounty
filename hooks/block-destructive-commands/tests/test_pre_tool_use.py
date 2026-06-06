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

    def test_allows_normal_commands(self):
        for command in (
            "ls -la",
            "git status",
            "npm test",
            "rm README.md",
            "git push origin main",
            "echo 'DELETE FROM backup' > notes.txt",
        ):
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


if __name__ == "__main__":
    unittest.main()
