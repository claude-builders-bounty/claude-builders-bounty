#!/usr/bin/env python3
"""
Unit tests for the audit logging subsystem (~/.claude/hooks/blocked.log).
"""

import sys
import os
import re
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK_SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "block_destructive.py"


class TestAuditLogging(unittest.TestCase):
    """Tests for log creation, format, timestamps, and path resolution."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "deep" / "nested" / "blocked.log"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook_with_command(self, cmd: str, env_override: dict = None) -> subprocess.CompletedProcess:
        payload = json.dumps({
            "tool_name": "Bash",
            "cwd": "/custom/project/path",
            "tool_input": {"command": cmd}
        })
        env = dict(os.environ)
        if env_override:
            env.update(env_override)
        else:
            env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)

        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            env=env
        )

    def test_log_file_and_directory_created(self):
        self.assertFalse(self.log_file.exists())
        proc = self.run_hook_with_command("rm -rf /")
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(self.log_file.exists())

    def test_log_entry_format_and_timestamp(self):
        proc = self.run_hook_with_command("DROP TABLE sensitive_data;")
        self.assertEqual(proc.returncode, 2)

        content = self.log_file.read_text(encoding="utf-8")
        # Format: [YYYY-MM-DDTHH:MM:SSZ] [CWD: ...] [RULE: drop_table] BLOCKED: ... | REASON: ...
        pattern = r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\] \[CWD: /custom/project/path\] \[RULE: drop_table\] BLOCKED: DROP TABLE sensitive_data; \| REASON: .+"
        self.assertRegex(content.strip(), pattern)

    def test_sequential_appending(self):
        commands = [
            "rm -rf /",
            "git push --force origin main",
            "TRUNCATE TABLE users;"
        ]
        for cmd in commands:
            proc = self.run_hook_with_command(cmd)
            self.assertEqual(proc.returncode, 2)

        content = self.log_file.read_text(encoding="utf-8")
        lines = [line for line in content.splitlines() if line.strip()]
        self.assertEqual(len(lines), 3)
        self.assertIn("rm_rf", lines[0])
        self.assertIn("git_force", lines[1])
        self.assertIn("truncate", lines[2])

    def test_safe_commands_do_not_log(self):
        proc = self.run_hook_with_command("git status")
        self.assertEqual(proc.returncode, 0)
        self.assertFalse(self.log_file.exists())

    def test_claude_blocked_log_path_env_var(self):
        alt_log = Path(self.temp_dir.name) / "alt_blocked.log"
        env = {"CLAUDE_BLOCKED_LOG_PATH": str(alt_log)}
        proc = self.run_hook_with_command("rm -rf node_modules", env_override=env)
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(alt_log.exists())
        self.assertIn("rm_rf", alt_log.read_text(encoding="utf-8"))

    def test_cli_log_file_argument(self):
        cli_log = Path(self.temp_dir.name) / "cli_blocked.log"
        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT), "--check", "rm -rf /", "--log-file", str(cli_log)],
            text=True,
            capture_output=True
        )
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(cli_log.exists())
        self.assertIn("rm_rf", cli_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
