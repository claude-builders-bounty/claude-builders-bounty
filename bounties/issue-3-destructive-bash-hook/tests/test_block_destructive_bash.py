from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_DIR = Path(__file__).resolve().parents[1]
HOOK_PATH = HOOK_DIR / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(hook)


def payload(command: str) -> dict[str, object]:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/workspace/app",
    }


class DestructiveBashHookTest(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked = {
            "rm -rf build": "rm -rf / rm -fr",
            "git push --force origin main": "git push --force",
            "psql -c 'DROP TABLE users'": "DROP TABLE",
            "sqlite3 app.db 'TRUNCATE audit_log'": "TRUNCATE",
            "psql -c 'DELETE FROM users'": "DELETE FROM without WHERE",
        }

        for command, reason in blocked.items():
            with self.subTest(command=command):
                self.assertEqual(hook.find_block_reason(command), reason)

    def test_allows_delete_from_with_where(self) -> None:
        self.assertIsNone(hook.find_block_reason("psql -c 'DELETE FROM users WHERE id = 42'"))

    def test_allows_normal_bash_commands(self) -> None:
        for command in ("git status", "npm test", "python -m unittest", "rm -r build"):
            with self.subTest(command=command):
                self.assertIsNone(hook.find_block_reason(command))

    def test_non_bash_tool_is_ignored(self) -> None:
        self.assertIsNone(hook.handle({"tool_name": "Read", "tool_input": {"file_path": "README.md"}}))

    def test_blocked_command_logs_json_line_and_denies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "blocked.log"
            previous = os.environ.get("CLAUDE_BLOCKED_LOG")
            os.environ["CLAUDE_BLOCKED_LOG"] = str(log_path)
            try:
                decision = hook.handle(payload("rm -rf dist"))
            finally:
                if previous is None:
                    os.environ.pop("CLAUDE_BLOCKED_LOG", None)
                else:
                    os.environ["CLAUDE_BLOCKED_LOG"] = previous

            self.assertIsNotNone(decision)
            output = decision["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")

            entries = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(entries), 1)
            entry = json.loads(entries[0])
            self.assertEqual(entry["attempted_command"], "rm -rf dist")
            self.assertEqual(entry["project_path"], "/workspace/app")
            self.assertEqual(entry["reason"], "rm -rf / rm -fr")
            self.assertIn("timestamp", entry)

    def test_cli_outputs_json_only_for_blocked_commands(self) -> None:
        env = os.environ.copy()
        with tempfile.TemporaryDirectory() as tmp_dir:
            env["CLAUDE_BLOCKED_LOG"] = str(Path(tmp_dir) / "blocked.log")

            blocked = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload("git push -f origin main")),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            self.assertIn('"permissionDecision": "deny"', blocked.stdout)

        safe = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload("git status")),
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        self.assertEqual(safe.stdout, "")


if __name__ == "__main__":
    unittest.main()
