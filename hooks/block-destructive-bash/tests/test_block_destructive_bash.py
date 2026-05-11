from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive_bash.py"


def run_hook(command: str, *, tool_name: str = "Bash") -> tuple[subprocess.CompletedProcess[str], Path]:
    log_dir = Path(tempfile.mkdtemp())
    log_path = log_dir / "blocked.log"
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["CLAUDE_BLOCKED_BASH_LOG"] = str(log_path)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    return result, log_path


class BlockDestructiveBashTest(unittest.TestCase):
    def assert_blocked(self, command: str, expected: str) -> None:
        result, log_path = run_hook(command)

        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected, output["permissionDecisionReason"])

        log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/example-project")
        self.assertIn(expected, log_entry["reason"])

    def assert_allowed(self, command: str, *, tool_name: str = "Bash") -> None:
        result, log_path = run_hook(command, tool_name=tool_name)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(log_path.exists())

    def test_allows_normal_bash_commands(self) -> None:
        self.assert_allowed("ls -la && git status --short")

    def test_ignores_non_bash_tools(self) -> None:
        self.assert_allowed("rm -rf /tmp/project", tool_name="Read")

    def test_blocks_recursive_force_rm_variants(self) -> None:
        self.assert_blocked("sudo rm -fr /tmp/project", "recursive force delete")

    def test_blocks_git_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")

    def test_allows_force_with_lease(self) -> None:
        self.assert_allowed("git push --force-with-lease origin main")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked('mysql -e "TRUNCATE TABLE sessions"', "TRUNCATE")

    def test_blocks_delete_from_without_where(self) -> None:
        self.assert_blocked('psql -c "DELETE FROM users"', "DELETE FROM")

    def test_allows_delete_from_with_where(self) -> None:
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')

    def test_sql_comment_cannot_fake_where_clause(self) -> None:
        self.assert_blocked('psql -c "DELETE FROM users -- WHERE id = 1"', "DELETE FROM")


if __name__ == "__main__":
    unittest.main()
