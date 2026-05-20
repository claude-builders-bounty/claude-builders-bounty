from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "block_destructive_bash.py"


def run_hook(command: str, log_path: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/work/project",
    }
    env = os.environ.copy()
    env["CLAUDE_BLOCKED_LOG"] = str(log_path)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashHookTests(unittest.TestCase):
    def test_allows_normal_bash_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            result = run_hook("npm test", log_path)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_blocks_rm_rf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            result = run_hook("rm -rf build", log_path)
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())

        decision = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            decision["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )
        self.assertIn("rm -rf", log_entry["reason"])
        self.assertEqual(log_entry["command"], "rm -rf build")

    def test_blocks_nested_shell_rm_rf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook('bash -c "rm -rf dist"', Path(tmp) / "blocked.log")

        self.assertIn("permissionDecision", result.stdout)

    def test_does_not_block_echoed_rm_rf_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook('echo "rm -rf dist"', Path(tmp) / "blocked.log")

        self.assertEqual(result.stdout, "")

    def test_blocks_git_push_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("git push --force origin main", Path(tmp) / "blocked.log")

        self.assertIn("force-pushing", result.stdout)

    def test_blocks_drop_table_and_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            drop = run_hook('psql -c "DROP TABLE users"', log_path)
            truncate = run_hook('psql -c "TRUNCATE TABLE sessions"', log_path)

        self.assertIn("DROP TABLE", drop.stdout)
        self.assertIn("TRUNCATE", truncate.stdout)

    def test_blocks_delete_from_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook('psql -c "DELETE FROM users;"', Path(tmp) / "blocked.log")

        self.assertIn("DELETE FROM", result.stdout)

    def test_allows_delete_from_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(
                'psql -c "DELETE FROM users WHERE id = 42;"',
                Path(tmp) / "blocked.log",
            )

        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
