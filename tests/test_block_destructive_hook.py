from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block-destructive" / "pre_tool_use.py"
spec = importlib.util.spec_from_file_location("block_destructive_hook", HOOK)
block_hook = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["block_destructive_hook"] = block_hook
spec.loader.exec_module(block_hook)


def payload(command: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/project",
        "tool_input": {"command": command},
    }


class BlockDestructiveHookTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        commands = [
            "rm -rf dist",
            "rm -fr build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "sqlite3 app.db 'TRUNCATE users'",
            "sqlite3 app.db 'DELETE FROM users'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(block_hook.blocked_reason(command))

    def test_allows_normal_bash_and_safe_delete(self) -> None:
        commands = [
            "npm test",
            "rm -r dist",
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(block_hook.blocked_reason(command))

    def test_logs_blocked_attempt_with_project_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = pathlib.Path(tmp) / "blocked.log"
            exit_code, message = block_hook.handle(payload("rm -rf /tmp/project"), log_path=log_path)
            log = log_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 2)
        self.assertIn("Blocked destructive Bash command", message)
        self.assertIn("/tmp/project", log)
        self.assertIn("rm -rf /tmp/project", log)

    def test_hook_process_exits_two_and_writes_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env["CLAUDE_BLOCK_HOOK_LOG"] = str(pathlib.Path(tmp) / "blocked.log")
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload("git push --force origin main")),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=env,
            )

        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("git push --force", proc.stderr)


if __name__ == "__main__":
    unittest.main()
