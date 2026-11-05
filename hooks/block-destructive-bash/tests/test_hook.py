#!/usr/bin/env python3
"""Tests for the block-destructive pre-tool-use hook (stdlib only)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE.parent / "block_destructive.py"
spec = importlib.util.spec_from_file_location("hook", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

BLOCK_COMMANDS = [
    "rm -rf /",
    "rm -fr ./build",
    "rm -r -f ./dist",
    "rm --recursive --force /var/data",
    "sudo rm -rf node_modules",
    "mysql -e 'DROP TABLE users'",
    "psql -c 'DROP DATABASE production'",
    "psql -c 'TRUNCATE TABLE orders'",
    "TRUNCATE users;",
    "sqlite3 app.db 'DELETE FROM customers'",
    "delete from logs",
    "git push --force origin main",
    "git push -f origin main",
    "mkfs.ext4 /dev/sda1",
    "dd if=/dev/zero of=/dev/sda bs=1M",
    ":(){ :|:& };:",
    "chmod -R 777 /var/www",
]

ALLOW_COMMANDS = [
    "ls -la",
    "npm run build",
    "git push origin main",
    "git push --force-with-lease origin main",
    "rm build/output.txt",
    "rm -r src/temp",
    "rm -f old.log",
    "DELETE FROM customers WHERE id = 3",
    "delete from audit_logs where created_at < '2024-01-01'",
    "grep -r TODO src/",
    "python manage.py migrate",
]


class TestRules(unittest.TestCase):
    def test_blocks_destructive_commands(self):
        for cmd in BLOCK_COMMANDS:
            self.assertIsNotNone(
                hook.check_command_safety(cmd),
                f"Expected to be blocked: {cmd}",
            )

    def test_allows_benign_commands(self):
        for cmd in ALLOW_COMMANDS:
            self.assertIsNone(
                hook.check_command_safety(cmd),
                f"Expected to be allowed: {cmd}",
            )


class TestProcessExecution(unittest.TestCase):
    def _run(self, payload: dict | str):
        inp = json.dumps(payload) if isinstance(payload, dict) else payload
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=inp,
            text=True,
            capture_output=True,
        )

    def test_blocked_exit_code_and_stderr(self):
        result = self._run({
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /test"},
            "cwd": "/tmp/project",
        })
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED BY PRE-TOOL HOOK", result.stderr)

    def test_allowed_exit_code(self):
        result = self._run({
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'Hello World'"},
            "cwd": "/tmp/project",
        })
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_non_bash_tool_ignored(self):
        result = self._run({
            "tool_name": "Read",
            "tool_input": {"file_path": "/etc/hosts"},
        })
        self.assertEqual(result.returncode, 0)

    def test_malformed_payload_fails_open(self):
        result = self._run("invalid json content")
        self.assertEqual(result.returncode, 0)

    def test_logs_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_log = Path(tmpdir) / "test_blocked.log"
            hook.LOG_PATH = test_log
            hook.write_log("test-reason", "rm -rf /", "/workspace/test")
            self.assertTrue(test_log.exists())
            content = test_log.read_text(encoding="utf-8")
            self.assertIn("test-reason", content)
            self.assertIn("rm -rf /", content)
            self.assertIn("/workspace/test", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
