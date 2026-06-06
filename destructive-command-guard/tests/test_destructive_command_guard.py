from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "destructive_command_guard.py"


def run_hook(
    command: str, cwd: str = "/tmp/project"
) -> tuple[subprocess.CompletedProcess[str], Path]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    }
    env = os.environ.copy()
    hooks_dir = Path(tempfile.mkdtemp())
    env["CLAUDE_HOOKS_DIR"] = str(hooks_dir)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    return result, hooks_dir


class DestructiveCommandGuardTests(unittest.TestCase):
    def assert_denied(self, command: str, expected: str) -> None:
        result, _hooks_dir = run_hook(command)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(expected, decision["permissionDecisionReason"])

    def test_allows_normal_bash_command(self) -> None:
        result, _hooks_dir = run_hook("npm test && git status")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_blocks_rm_rf(self) -> None:
        self.assert_denied("rm -rf dist", "rm -rf")

    def test_blocks_force_push(self) -> None:
        self.assert_denied("git push origin main --force", "forced git push")

    def test_blocks_drop_table(self) -> None:
        self.assert_denied('psql -c "DROP TABLE users"', "DROP TABLE")

    def test_blocks_truncate(self) -> None:
        self.assert_denied('mysql -e "TRUNCATE sessions"', "TRUNCATE")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_denied('psql -c "DELETE FROM accounts;"', "DELETE FROM")

    def test_allows_delete_with_where(self) -> None:
        result, _hooks_dir = run_hook('psql -c "DELETE FROM accounts WHERE id = 1;"')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_logs_blocked_attempt_as_jsonl(self) -> None:
        command = "rm -rf build"
        project_path = "/tmp/project-alpha"
        result, hooks_dir = run_hook(command, cwd=project_path)
        self.assertEqual(result.returncode, 0)

        log_path = hooks_dir / "blocked.log"
        self.assertTrue(log_path.exists())
        record = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertIn("timestamp", record)
        self.assertEqual(record["command"], command)
        self.assertEqual(record["project_path"], project_path)
        self.assertIn("rm -rf", record["reason"])


if __name__ == "__main__":
    unittest.main()
