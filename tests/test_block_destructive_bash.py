from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


class DestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/workspace/project",
        }
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        env = os.environ.copy()
        env["CLAUDE_HOOK_HOME"] = self.tmpdir.name
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def assertBlocked(self, command: str, reason_fragment: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        decision = json.loads(result.stdout)
        output = decision["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(reason_fragment, output["permissionDecisionReason"])

        log_path = Path(self.tmpdir.name) / "blocked.log"
        self.assertTrue(log_path.exists())
        log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["project_path"], "/workspace/project")

    def assertAllowed(self, command: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse((Path(self.tmpdir.name) / "blocked.log").exists())

    def test_blocks_required_destructive_patterns(self) -> None:
        cases = [
            ("rm -rf build", "rm -rf"),
            ("sudo rm -r -f /tmp/project", "rm -rf"),
            ("cd build && rm -fr dist", "rm -rf"),
            ("git push --force origin main", "force-pushing"),
            ("git -C repo push --force origin main", "force-pushing"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("psql -c 'TRUNCATE sessions'", "TRUNCATE"),
            ("psql -c 'DELETE FROM users'", "without a WHERE"),
        ]
        for command, reason in cases:
            with self.subTest(command=command):
                self.assertBlocked(command, reason)

    def test_allows_normal_bash_commands(self) -> None:
        cases = (
            "npm test",
            "git push origin main",
            "rm build.log",
            "psql -c 'DELETE FROM users WHERE id = 1'",
        )
        for command in cases:
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_ignores_non_bash_tools(self) -> None:
        result = self.run_hook("rm -rf build", tool_name="Read")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
