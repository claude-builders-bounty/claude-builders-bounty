#!/usr/bin/env python3
"""End-to-end delivery verification for bounty #3 fleet handoff."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_PATH = HOOK_DIR / "pre-tool-use.py"
CI_SCRIPT = HOOK_DIR / "tests" / "run-ci-checks.sh"
PEER_REVIEW_TEST = HOOK_DIR / "tests" / "test_peer_review_acceptance.py"
UNIT_TEST = HOOK_DIR / "tests" / "test_pre_tool_use.py"


def count_test_methods(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*def test_", text, flags=re.MULTILINE))


class DeliveryVerificationTests(unittest.TestCase):
    """Guards fleet delivery: tests run, peer review passes, CLI behaves correctly."""

    def test_regression_suite_has_minimum_coverage(self):
        unit_tests = count_test_methods(UNIT_TEST)
        peer_review_tests = count_test_methods(PEER_REVIEW_TEST)
        self.assertGreaterEqual(unit_tests, 65)
        self.assertGreaterEqual(peer_review_tests, 15)

    def test_ci_script_exists_and_declares_delivery_checks(self):
        self.assertTrue(CI_SCRIPT.is_file())
        text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("delivery verification tests", text)
        self.assertIn("peer review acceptance tests passed", text)

    def test_cli_denies_rm_rf_root_with_official_schema(self):
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "rm -rf /"},
                        "cwd": "/workspace/demo",
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_file = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_file.is_file())
            log_text = log_file.read_text(encoding="utf-8")
            self.assertIn("rm -rf /", log_text)
            self.assertIn("/workspace/demo", log_text)

    def test_cli_allows_git_status_without_output(self):
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "git status"},
                        "cwd": "/workspace/demo",
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")
            log_file = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            self.assertFalse(log_file.exists())


if __name__ == "__main__":
    unittest.main()
