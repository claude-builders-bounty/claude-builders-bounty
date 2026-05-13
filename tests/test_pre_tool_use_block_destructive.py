from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_block_destructive.py"


class PreToolUseBlockDestructiveTests(unittest.TestCase):
    def run_hook(self, command: str) -> tuple[int, dict[str, str], Path]:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        log_path = Path(tmpdir.name) / "blocked.log"
        env = os.environ.copy()
        env["CLAUDE_BLOCKED_LOG"] = str(log_path)
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        return proc.returncode, json.loads(proc.stdout), log_path

    def assert_blocked(self, command: str, expected_reason_part: str) -> None:
        code, output, log_path = self.run_hook(command)
        self.assertNotEqual(code, 0)
        self.assertEqual(output["decision"], "block")
        self.assertIn(expected_reason_part, output["reason"])
        self.assertTrue(log_path.exists())
        entries = log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(entries), 1)
        entry = json.loads(entries[0])
        self.assertEqual(entry["command"], command)
        self.assertIn(expected_reason_part, entry["reason"])
        self.assertIn("timestamp", entry)

    def assert_allowed(self, command: str) -> None:
        code, output, log_path = self.run_hook(command)
        self.assertEqual(code, 0)
        self.assertEqual(output, {"decision": "approve"})
        self.assertFalse(log_path.exists())

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "recursive forced deletion")
        self.assert_blocked("rm -fr build", "recursive forced deletion")
        self.assert_blocked("rm --recursive --force build", "recursive forced deletion")

    def test_blocks_sql_destructive_statements(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE")
        self.assert_blocked("mysql -e 'DELETE FROM users'", "DELETE FROM without a WHERE")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed("mysql -e 'DELETE FROM users WHERE id = 42'")

    def test_blocks_forced_git_pushes(self) -> None:
        self.assert_blocked("git push --force origin main", "forced git pushes")
        self.assert_blocked("git push -f origin main", "forced git pushes")
        self.assert_blocked("git push --force-with-lease origin main", "forced git pushes")

    def test_allows_safe_commands(self) -> None:
        self.assert_allowed("git push origin feature-branch")
        self.assert_allowed("rm -r build")
        self.assert_allowed("python -m pytest")

    def test_blocks_invalid_json(self) -> None:
        env = os.environ.copy()
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not-json",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        output = json.loads(proc.stdout)
        self.assertEqual(output["decision"], "block")
        self.assertIn("Invalid hook JSON", output["reason"])


if __name__ == "__main__":
    unittest.main()
