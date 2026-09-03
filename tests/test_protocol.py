#!/usr/bin/env python3
"""
Unit tests for the Claude Code PreToolUse hook IPC protocol and CLI interface.
"""

import sys
import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK_SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "block_destructive.py"


class TestClaudeCodeProtocol(unittest.TestCase):
    """Tests for stdin/stdout JSON protocol and exit code contracts."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "blocked.log"
        self.env = dict(os.environ)
        self.env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook(self, payload: str = None, args: list = None) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(HOOK_SCRIPT)]
        if args:
            cmd.extend(args)
        return subprocess.run(
            cmd,
            input=payload,
            text=True,
            capture_output=True,
            env=self.env
        )

    def test_destructive_bash_command_exits_2(self):
        payload = json.dumps({
            "tool_name": "Bash",
            "cwd": "/test/project",
            "tool_input": {"command": "rm -rf /"}
        })
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("SECURITY HOOK BLOCKED", proc.stderr)
        self.assertIn("rm_rf", proc.stderr)

        # Validate stdout JSON
        data = json.loads(proc.stdout)
        decision = data["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")

    def test_safe_bash_command_exits_0(self):
        payload = json.dumps({
            "tool_name": "Bash",
            "cwd": "/test/project",
            "tool_input": {"command": "git status"}
        })
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, "")

        data = json.loads(proc.stdout)
        decision = data["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "allow")

    def test_non_bash_tool_ignored(self):
        # Even with destructive command, non-bash tools bypass the hook
        payload = json.dumps({
            "tool_name": "Edit",
            "cwd": "/test/project",
            "tool_input": {"command": "rm -rf /"}
        })
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)

    def test_empty_stdin_exits_0(self):
        proc = self.run_hook("")
        self.assertEqual(proc.returncode, 0)

    def test_whitespace_stdin_exits_0(self):
        proc = self.run_hook("   \n\t  ")
        self.assertEqual(proc.returncode, 0)

    def test_malformed_json_exits_0(self):
        proc = self.run_hook("{ bad json }")
        self.assertEqual(proc.returncode, 0)

    def test_non_dict_json_exits_0(self):
        proc = self.run_hook("[1, 2, 3]")
        self.assertEqual(proc.returncode, 0)

    def test_missing_tool_input_exits_0(self):
        payload = json.dumps({"tool_name": "Bash"})
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)

    def test_missing_command_field_exits_0(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {}})
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)

    def test_non_string_command_field_exits_0(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": 12345}})
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)


class TestCliInterface(unittest.TestCase):
    """Tests for direct CLI check mode."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "blocked.log"
        self.env = dict(os.environ)
        self.env["CLAUDE_HOOK_BLOCKED_LOG"] = str(self.log_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, args: list) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(HOOK_SCRIPT)] + args
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            env=self.env
        )

    def test_cli_check_destructive_exits_2(self):
        proc = self.run_cli(["--check", "DROP TABLE users;"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("SECURITY HOOK BLOCKED", proc.stderr)
        self.assertIn("drop_table", proc.stderr)

    def test_cli_check_safe_exits_0(self):
        proc = self.run_cli(["--check", "npm test"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ALLOWED", proc.stdout)

    def test_cli_help_exits_0(self):
        proc = self.run_cli(["--help"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Claude Code PreToolUse Hook", proc.stdout)


if __name__ == "__main__":
    unittest.main()
