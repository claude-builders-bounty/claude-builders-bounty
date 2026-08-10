#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive_commands.py"


def run_hook(command=None, tool_name="Bash", payload=None, log_path=None):
    if payload is None:
        payload = {"tool_name": tool_name, "tool_input": {"command": command}, "cwd": "/tmp/project"}
    env = os.environ.copy()
    if log_path:
        env["CLAUDE_HOOK_LOG"] = str(log_path)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload) if payload is not None else "",
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    return result


class HookTests(unittest.TestCase):
    def test_blocks_rm_variants(self):
        for command in ("rm -rf build", "rm -fr build", "rm -r -f build", "rm --recursive --force build"):
            with self.subTest(command=command):
                self.assertIn('"permissionDecision": "deny"', run_hook(command).stdout)

    def test_blocks_forced_push_variants(self):
        for command in ("git push --force origin main", "git push -f origin main"):
            with self.subTest(command=command):
                self.assertIn('"permissionDecision": "deny"', run_hook(command).stdout)

    def test_blocks_sql_destructive_commands(self):
        for command in ("DROP TABLE users", "truncate table users", "DELETE FROM users"):
            with self.subTest(command=command):
                self.assertIn('"permissionDecision": "deny"', run_hook(command).stdout)

    def test_allows_safe_commands(self):
        for command in (
            "rm file.txt",
            "rm -f file.txt",
            "git push origin main",
            "DELETE FROM users WHERE id = 1",
            "SELECT * FROM users",
            "echo 'DROP TABLE users'",
        ):
            with self.subTest(command=command):
                self.assertEqual(run_hook(command).stdout, "")

    def test_ignores_non_bash_tools(self):
        self.assertEqual(run_hook("rm -rf /tmp/x", tool_name="Read").stdout, "")

    def test_malformed_input_is_allowed(self):
        result = subprocess.run([sys.executable, str(HOOK)], input="not json", text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_denial_is_logged(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "blocked.log"
            result = run_hook("rm -rf build", log_path=log_path)
            self.assertEqual(result.returncode, 0)
            record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["command"], "rm -rf build")
            self.assertEqual(record["project_path"], "/tmp/project")
            self.assertIn("blocked", record["reason"])
            self.assertTrue(record["timestamp"])


if __name__ == "__main__":
    unittest.main()
