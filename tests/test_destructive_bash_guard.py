from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / "hooks" / "destructive_bash_guard.py"

spec = importlib.util.spec_from_file_location("destructive_bash_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class DestructiveBashGuardTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked_commands = [
            "rm -rf build",
            "sudo rm -fr /tmp/project",
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'TRUNCATE sessions'",
            "git push --force origin main",
            "git push -f origin main",
            "psql -c 'DELETE FROM users'",
        ]

        for command in blocked_commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_allows_normal_commands_and_scoped_delete(self) -> None:
        allowed_commands = [
            "npm test",
            "git status --short",
            "rm -r build",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "git push origin feature/safe-branch",
        ]

        for command in allowed_commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command))

    def test_hook_exits_2_and_logs_blocked_command(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": "rm -rf build"},
        }
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked destructive Bash command", result.stderr)

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_record["command"], "rm -rf build")
            self.assertEqual(log_record["project_path"], "/tmp/project")

    def test_non_bash_tool_is_ignored(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps({"tool_name": "Read", "tool_input": {"command": "rm -rf build"}}),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
