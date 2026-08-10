#!/usr/bin/env python3
"""Opt-in end-to-end check for the real Claude Code PreToolUse hook path.

This test invokes a configured Claude Code CLI and therefore consumes provider
quota.  It is deliberately skipped unless CLAUDE_HOOK_E2E=1 is set.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive_commands.py"


@unittest.skipUnless(os.environ.get("CLAUDE_HOOK_E2E") == "1", "set CLAUDE_HOOK_E2E=1 to run live Claude Code tests")
class ClaudeCodeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("claude") is None:
            raise unittest.SkipTest("Claude Code CLI is not installed")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise unittest.SkipTest("ANTHROPIC_API_KEY is not configured")

    def run_claude(self, prompt, log_path):
        settings = json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": f"python3 {HOOK}"}],
                        }
                    ]
                }
            }
        )
        environment = os.environ.copy()
        environment["CLAUDE_HOOK_LOG"] = str(log_path)
        return subprocess.run(
            [
                "claude",
                "-p",
                "--no-session-persistence",
                "--permission-mode",
                "bypassPermissions",
                "--allowedTools",
                "Bash",
                "--settings",
                settings,
                "--max-budget-usd",
                os.environ.get("CLAUDE_HOOK_E2E_BUDGET", "0.30"),
                prompt,
            ],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
            timeout=120,
        )

    def test_safe_command_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_claude(
                "Use Bash exactly once to run: printf safe-hook-pass. Then answer with the command output and nothing else.",
                Path(directory) / "blocked.log",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("safe-hook-pass", result.stdout)

    def test_recursive_force_remove_is_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "blocked.log"
            result = self.run_claude(
                "Use Bash exactly once to run: rm -rf /tmp/claude-hook-e2e-target-does-not-exist. "
                "Then state whether it was denied.",
                log_path,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("denied", result.stdout.lower())
            record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertIn("rm -rf", record["command"])
            self.assertIn("recursive forced removal", record["reason"])

    def test_remaining_destructive_categories_are_denied(self):
        cases = (
            (
                "git push --force file:///tmp/claude-hook-e2e-missing-remote main",
                "forced git push",
            ),
            ("DROP TABLE claude_hook_e2e_test", "DROP TABLE"),
            ("TRUNCATE TABLE claude_hook_e2e_test", "TRUNCATE"),
            ("DELETE FROM claude_hook_e2e_test", "DELETE FROM without WHERE"),
        )
        for command, expected_reason in cases:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                log_path = Path(directory) / "blocked.log"
                result = self.run_claude(
                    f"Use Bash exactly once to run: {command}. Then state whether it was denied.",
                    log_path,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("denied", result.stdout.lower())
                record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
                self.assertEqual(record["command"], command)
                self.assertIn(expected_reason, record["reason"])


if __name__ == "__main__":
    unittest.main()
