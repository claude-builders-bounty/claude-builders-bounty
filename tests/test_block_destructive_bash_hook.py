#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block-destructive-bash" / "block_destructive_bash.py"


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    event = {
        "tool_name": "Bash",
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }
    with tempfile.TemporaryDirectory() as home:
        return subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env={"HOME": home, "PATH": "/usr/bin:/bin"},
            check=False,
        )


class BlockDestructiveBashHookTest(unittest.TestCase):
    def assert_blocked(self, command: str) -> None:
        result = run_hook(command)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("Blocked destructive Bash command", result.stderr)

    def assert_allowed(self, command: str) -> None:
        result = run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocks_recursive_force_deletion(self) -> None:
        self.assert_blocked("rm -rf build")
        self.assert_blocked("rm -fr build")

    def test_blocks_force_push(self) -> None:
        self.assert_blocked("git push origin main --force")
        self.assert_blocked("git push -f origin main")
        self.assert_blocked("git push --force-with-lease")
        self.assert_blocked("cd repo && git push origin main --force")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'")
        self.assert_blocked("psql -c 'TRUNCATE users'")
        self.assert_blocked("psql -c 'DELETE FROM users'")

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("rm build/output.log")
        self.assert_allowed("git push origin feature")
        self.assert_allowed("psql -c 'DELETE FROM users WHERE id = 1'")
        self.assert_allowed("npm test")


if __name__ == "__main__":
    unittest.main()
