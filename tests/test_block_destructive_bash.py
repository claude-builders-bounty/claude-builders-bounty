#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block-destructive-bash" / "block_destructive_bash.py"


class BlockDestructiveBashTests(unittest.TestCase):
    def run_hook(self, command: str, home: Path) -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        return subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env={"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        )

    def assert_blocked(self, command: str, expected: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_hook(command, Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertIn('"permissionDecision": "deny"', result.stdout)
            self.assertIn(expected, result.stdout)

            log_path = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(log_entry["attempted_command"], command)
            self.assertEqual(log_entry["project_path"], "/tmp/example-project")

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf build", "rm -rf style recursive forced deletion")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE statement")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked('mysql -e "TRUNCATE audit_log"', "TRUNCATE statement")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_blocked('psql -c "DELETE FROM sessions"', "DELETE FROM statement without WHERE clause")

    def test_allows_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_hook('psql -c "DELETE FROM sessions WHERE id = 1"', Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push origin main --force", "git force push")

    def test_allows_safe_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_hook("git status && npm test", Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(tmp) / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
