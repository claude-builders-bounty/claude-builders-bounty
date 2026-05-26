from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block_destructive_bash.py"


def run_hook(
    command: str,
    cwd: str | None = None,
    hooks_dir: str | None = None,
) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    if cwd is not None:
        payload["cwd"] = cwd

    env = os.environ.copy()
    if hooks_dir is not None:
        env["CLAUDE_HOOKS_DIR"] = hooks_dir

    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


class BlockDestructiveBashTest(unittest.TestCase):
    def test_allows_safe_commands(self) -> None:
        for command in ("ls -la", "git status", "npm test", "python -m pytest"):
            with self.subTest(command=command):
                result = run_hook(command)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")

    def test_blocks_recursive_forced_remove(self) -> None:
        for command in ("rm -rf /tmp/build", "sudo rm -rf /tmp/build", "rm -r -f /tmp/build"):
            with self.subTest(command=command):
                result = run_hook(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("recursive forced deletion", result.stderr)

    def test_blocks_drop_table(self) -> None:
        result = run_hook("psql -c 'DROP TABLE users'")
        self.assertEqual(result.returncode, 2)
        self.assertIn("SQL DROP TABLE", result.stderr)

    def test_blocks_force_push(self) -> None:
        for command in (
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease",
        ):
            with self.subTest(command=command):
                result = run_hook(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("force push", result.stderr)

    def test_blocks_truncate(self) -> None:
        result = run_hook("mysql -e 'TRUNCATE TABLE audit_log'")
        self.assertEqual(result.returncode, 2)
        self.assertIn("SQL TRUNCATE", result.stderr)

    def test_blocks_delete_without_where(self) -> None:
        result = run_hook("psql -c 'DELETE FROM users'")
        self.assertEqual(result.returncode, 2)
        self.assertIn("DELETE statement without WHERE", result.stderr)

    def test_allows_delete_with_where(self) -> None:
        result = run_hook("psql -c 'DELETE FROM users WHERE id = 1'")
        self.assertEqual(result.returncode, 0)

    def test_ignores_non_bash_tools(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md"},
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_writes_blocked_log_in_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as hooks_dir:
            result = run_hook("git push --force origin main", cwd=temp_dir, hooks_dir=hooks_dir)
            log_path = Path(hooks_dir) / "blocked.log"

            self.assertEqual(result.returncode, 2)
            self.assertTrue(log_path.exists())

            entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["project_path"], temp_dir)
            self.assertEqual(entry["reason"], "force push")
            self.assertEqual(entry["command"], "git push --force origin main")
            self.assertIn("timestamp", entry)


if __name__ == "__main__":
    unittest.main()
