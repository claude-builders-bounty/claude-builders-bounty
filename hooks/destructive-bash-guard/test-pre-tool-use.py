#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("pre-tool-use.py")
sys.path.insert(0, str(Path(__file__).resolve().parent))

module_spec = importlib.util.spec_from_file_location("destructive_pre_tool_use", SCRIPT)
pre_tool_use = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(pre_tool_use)


def invoke(command: str) -> tuple[int, str, str]:
    payload = json.dumps(
        {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/project",
        }
    )
    process = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=payload,
        text=True,
        capture_output=True,
        env={"HOME": tempfile.mkdtemp(), "PATH": "/usr/bin:/bin"},
        check=False,
        timeout=5,
    )
    return process.returncode, process.stdout, process.stderr


class DestructiveBashGuardTests(unittest.TestCase):
    def test_normal_commands_are_allowed(self) -> None:
        for command in (
            "ls -la",
            "git status",
            "echo 'DROP TABLE users'",
            "grep -R 'DELETE FROM users' .",
            "echo 'rm -rf /tmp'",
            "echo rm -rf /tmp",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "git push --force-with-lease origin main",
        ):
            with self.subTest(command=command):
                returncode, stdout, stderr = invoke(command)
                self.assertEqual(returncode, 0, stderr)
                self.assertEqual(stdout, "")

    def test_required_destructive_patterns_are_blocked(self) -> None:
        cases = {
            "rm -rf /tmp/example": "rm",
            "sudo rm -rf /tmp/example": "rm",
            "rm -r --force /tmp/example": "rm",
            "rm -fr /tmp/example": "rm",
            "git push --force origin main": "git push",
            "git push -f origin main": "git push",
            "psql -c 'DROP TABLE users'": "DROP TABLE",
            "mysql -e 'TRUNCATE users'": "TRUNCATE",
            "sqlite3 app.db 'DELETE FROM users'": "DELETE",
            "echo ready && psql -c 'DELETE FROM users'": "DELETE",
            "bash -c 'rm -rf /tmp/example'": "rm",
            "bash -c 'psql -c \"DELETE FROM users\"'": "DELETE",
        }
        for command, expected_text in cases.items():
            with self.subTest(command=command):
                returncode, stdout, stderr = invoke(command)
                self.assertEqual(returncode, 0, stderr)
                output = json.loads(stdout)
                self.assertEqual(
                    output["hookSpecificOutput"]["permissionDecision"],
                    "deny",
                )
                self.assertIn(expected_text, output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_block_is_logged(self) -> None:
        home = tempfile.mkdtemp()
        payload = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /tmp/example"},
                "cwd": "/project",
            }
        )
        process = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            env={"HOME": home, "PATH": "/usr/bin:/bin"},
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        log_file = Path(home) / ".claude" / "hooks" / "blocked.log"
        entries = [json.loads(line) for line in log_file.read_text().splitlines()]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["attempted_command"], "rm -rf /tmp/example")
        self.assertEqual(entries[0]["project_path"], "/project")
        self.assertIn("timestamp", entries[0])

    def test_non_bash_tools_are_allowed(self) -> None:
        self.assertIsNone(pre_tool_use.run({"tool_name": "Read"}))

    def test_viewer_commands_do_not_execute_embedded_destructive_text(self) -> None:
        self.assertIsNone(pre_tool_use.inspect_command("echo 'psql -c \"DROP TABLE users\"'"))


if __name__ == "__main__":
    unittest.main()
