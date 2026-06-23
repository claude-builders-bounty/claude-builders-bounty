from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "block_destructive_bash.py"


def run_hook(home: Path, command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {"tool_name": tool_name, "tool_input": {"command": command}, "cwd": str(home)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={"USERPROFILE": str(home), "HOME": str(home)},
        check=False,
    )


def assert_denied(result: subprocess.CompletedProcess[str], reason: str) -> None:
    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert reason in hook_output["permissionDecisionReason"]


class BlockDestructiveBashTest(unittest.TestCase):
    def test_blocks_recursive_force_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(Path(tmp), "rm -rf build")
        assert_denied(result, "recursive force removal")

    def test_blocks_force_push(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(Path(tmp), "git push origin main --force-with-lease")
        assert_denied(result, "force push")

    def test_blocks_sql_delete_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(Path(tmp), 'psql -c "DELETE FROM users"')
        assert_denied(result, "delete statement without WHERE")

    def test_allows_sql_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(Path(tmp), 'psql -c "DELETE FROM users WHERE id = 1"')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_allows_non_bash_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook(Path(tmp), "rm -rf build", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_writes_blocked_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            run_hook(home, "DROP TABLE users")
            log_file = home / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log_file.read_text(encoding="utf-8").strip())
            self.assertEqual(record["reason"], "table drop")
            self.assertEqual(record["project_path"], str(home))
            self.assertEqual(record["command"], "DROP TABLE users")


if __name__ == "__main__":
    unittest.main()
