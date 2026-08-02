from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block_destructive.py"


class DestructiveHookTests(unittest.TestCase):
    def run_hook(self, command: str, *, tool_name: str = "Bash") -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "tool_name": tool_name,
                "tool_input": {"command": command},
                "cwd": str(ROOT),
            }
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            env["CLAUDE_HOOK_HOME"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_content = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            return result.returncode, result.stdout, log_content

    def test_blocks_required_patterns_with_structured_deny(self) -> None:
        commands = [
            "rm -rf ./build",
            "git push origin main --force",
            "DROP TABLE accounts",
            "TRUNCATE TABLE sessions",
            "DELETE FROM users",
        ]
        for command in commands:
            with self.subTest(command=command):
                code, output, log_content = self.run_hook(command)
                self.assertEqual(code, 0)
                decision = json.loads(output)
                specific = decision["hookSpecificOutput"]
                self.assertEqual(specific["hookEventName"], "PreToolUse")
                self.assertEqual(specific["permissionDecision"], "deny")
                self.assertIn("Destructive command blocked", specific["permissionDecisionReason"])
                self.assertIn(command, log_content)

    def test_allows_safe_commands_and_delete_with_where(self) -> None:
        for command in (
            "rm ./build.log",
            "git push origin main",
            "DELETE FROM users WHERE id = 7",
            "SELECT * FROM users",
        ):
            with self.subTest(command=command):
                code, output, log_content = self.run_hook(command)
                self.assertEqual(code, 0)
                self.assertEqual(output, "")
                self.assertEqual(log_content, "")

    def test_delete_is_checked_per_statement(self) -> None:
        code, output, _ = self.run_hook("DELETE FROM users; SELECT * FROM users WHERE id = 7")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_ignores_non_bash_tools(self) -> None:
        code, output, log_content = self.run_hook("rm -rf ./build", tool_name="Read")
        self.assertEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(log_content, "")


if __name__ == "__main__":
    unittest.main()
