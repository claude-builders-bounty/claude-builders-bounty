from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive.py"


class BlockDestructiveTests(unittest.TestCase):
    def run_hook(self, command: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as home:
            return self.run_hook_with_home(command, Path(home))

    def run_hook_with_home(self, command: str, home: Path) -> subprocess.CompletedProcess[str]:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env={"HOME": str(home), "USERPROFILE": str(home), "PATH": ""},
            check=False,
        )

    def assert_blocked(self, command: str, expected_rule: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertIn("permissionDecision", result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn(expected_rule, payload["hookSpecificOutput"]["permissionDecisionReason"].lower())

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf build", "recursive force")
        self.assert_blocked("rm -fr build", "recursive force")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "drop table")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push --force origin main", "force")
        self.assert_blocked("git push -f origin main", "force")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked('mysql -e "TRUNCATE users"', "truncate")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_blocked('psql -c "DELETE FROM users"', "delete from")

    def test_allows_delete_with_where(self) -> None:
        result = self.run_hook('psql -c "DELETE FROM users WHERE id = 1"')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_allows_normal_bash(self) -> None:
        result = self.run_hook("npm test && git status")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_writes_blocked_log(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            result = self.run_hook_with_home("rm -rf build", home_path)
            self.assertEqual(result.returncode, 0)
            log_path = home_path / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["attempted_command"], "rm -rf build")
            self.assertEqual(record["project_path"], "/tmp/example-project")
            self.assertEqual(record["rule"], "rm-rf")


if __name__ == "__main__":
    unittest.main()
