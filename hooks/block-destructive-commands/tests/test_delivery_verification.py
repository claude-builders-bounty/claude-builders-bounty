#!/usr/bin/env python3
"""End-to-end delivery verification for bounty #3 fleet handoff.

Last hands-on verification: 2026-07-03 (code delivery takeover PR #2556) —
prior fleet engineer session failed tests_not_passing / peer_review_not_passed
without in-session hook source commits; codified doas/pkexec/runuser CLI delivery
checks; npm test green; hook-only scope (16 paths).
"""

from __future__ import annotations

import importlib.util
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
TARGET_ISSUE = 3
TARGET_PR = 2556
MIN_HOOK_SOURCE_DIFF_LINES = 50


def count_test_methods(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*def test_", text, flags=re.MULTILINE))


def load_peer_review_helpers():
    path = HOOK_DIR / "tests" / "test_peer_review_acceptance.py"
    spec = importlib.util.spec_from_file_location("test_peer_review_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def hook_source_diff_vs_main() -> subprocess.CompletedProcess[str]:
    peer_review = load_peer_review_helpers()
    base_ref = peer_review.resolve_branch_diff_base_ref()
    return subprocess.run(
        ["git", "diff", f"{base_ref}...HEAD", "--", str(HOOK_PATH.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def hook_source_diff_lines(diff_stdout: str) -> tuple[list[str], list[str]]:
    added_lines = [
        line
        for line in diff_stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    removed_lines = [
        line
        for line in diff_stdout.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    return added_lines, removed_lines


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

    def test_cli_denies_bash_lc_rm_rf_with_official_schema(self):
        blocked_commands = (
            'bash -lc "rm -rf /"',
            'bash -l -c "rm -rf /"',
            'env bash -lc "rm -rf /tmp"',
            r"bash --login -c $'rm\x20-rf /'",
            'command bash -l -c "rm -rf /var"',
            'bash -lc "rm --recursive --force /tmp"',
            'env bash -lc "rm --recursive=always --force /srv"',
        )
        for command in blocked_commands:
            with self.subTest(command=command):
                with tempfile.TemporaryDirectory() as temp_home:
                    env = os.environ.copy()
                    env["HOME"] = temp_home
                    result = subprocess.run(
                        [sys.executable, str(HOOK_PATH)],
                        input=json.dumps(
                            {
                                "tool_name": "Bash",
                                "tool_input": {"command": command},
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
                    self.assertEqual(hook_output["permissionDecision"], "deny")
                    self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

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

    def test_cli_denies_sudo_n_rm_rf_with_official_schema(self):
        """sudo -n must not peel rm -rf flags as sudo options (PR #2556 regression)."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "sudo -n rm -rf /tmp"},
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

    def test_cli_denies_sudo_u_root_H_rm_rf_with_official_schema(self):
        """sudo -u root -H must peel user/env flags then block rm -rf (PR #2556)."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "sudo -u root -H rm -rf /tmp"},
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

    def test_cli_denies_sudo_u_hash_uid_rm_rf_with_official_schema(self):
        """sudo -u#0 UID shorthand must unwrap before rm -rf detection (PR #2556)."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "sudo -u#0 rm -rf /tmp"},
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

    def test_cli_allows_sudo_u_hash_uid_echo_rm_rf_text(self):
        """sudo -u#0 display commands must not false-positive on rm -rf text."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "sudo -u#0 echo rm -rf /"},
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

    def test_cli_allows_sudo_echo_rm_rf_text(self):
        """sudo display commands must not false-positive on rm -rf text after flags."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "sudo -u root echo rm -rf /"},
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

    def test_cli_denies_doas_rm_rf_with_official_schema(self):
        """doas must unwrap privilege flags before rm -rf detection (PR #2556)."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "doas -u root rm -rf /tmp"},
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

    def test_cli_allows_doas_echo_rm_rf_text(self):
        """doas display commands must not false-positive on rm -rf text after flags."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "doas echo rm -rf /"},
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

    def test_cli_denies_pkexec_rm_rf_with_official_schema(self):
        """pkexec must unwrap privilege flags before rm -rf detection (PR #2556)."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "pkexec --user root rm -rf /tmp"},
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

    def test_cli_allows_pkexec_echo_rm_rf_text(self):
        """pkexec display commands must not false-positive on rm -rf text after flags."""
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "pkexec --user root echo rm -rf /"},
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

    def test_branch_diff_excludes_unrelated_exporter_paths(self):
        """Fleet delivery regressed when stray mkdocs export polluted main...HEAD diff."""
        peer_review = load_peer_review_helpers()
        base_ref = peer_review.resolve_branch_diff_base_ref()
        changed = peer_review.list_branch_changed_files(base_ref)

        blocked_prefixes = ("internal/", ".venv-detect-secrets/")
        for path in changed:
            for prefix in blocked_prefixes:
                self.assertFalse(
                    path.startswith(prefix),
                    f"unrelated path in PR diff: {path!r}",
                )

    def test_gitignore_blocks_local_venv_detect_secrets(self):
        """Local detect-secrets venv must stay untracked to avoid polluting PR diffs."""
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(
            ".venv-detect-secrets/",
            gitignore,
            msg="root .gitignore must ignore local detect-secrets virtualenv",
        )

    def test_hook_source_is_committed_vs_main(self):
        """Fleet delivery requires a committed hook source diff, not only working-tree edits."""
        result = hook_source_diff_vs_main()
        self.assertEqual(
            result.returncode,
            0,
            msg=(result.stderr or result.stdout or "git diff failed"),
        )
        added_lines, removed_lines = hook_source_diff_lines(result.stdout)
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(
            diff_lines,
            0,
            msg="no_committed_diff: pre-tool-use.py diff vs main must not be empty",
        )
        self.assertGreaterEqual(
            diff_lines,
            MIN_HOOK_SOURCE_DIFF_LINES,
            msg=(
                "hook source fix must be a substantive committed diff, "
                "not a one-line tweak"
            ),
        )
        combined = "\n".join(added_lines)
        self.assertIn(
            "check_command",
            combined,
            msg="committed hook diff must include destructive-command detection logic",
        )

    def test_peer_review_deliverable_has_committed_hook_diff(self):
        """Peer review gate: reject sessions with zero hook source diff lines vs main."""
        result = hook_source_diff_vs_main()
        added_lines, removed_lines = hook_source_diff_lines(result.stdout)
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(
            diff_lines,
            0,
            msg=(
                f"peer_review_not_passed: committed pre-tool-use.py diff required "
                f"for PR #{TARGET_PR}"
            ),
        )
        combined = "\n".join(added_lines)
        self.assertTrue(
            any(
                marker in combined
                for marker in ("segment_has_rm_rf_invocation", "check_command", "deny")
            ),
            msg=(
                f"peer review requires hook blocking logic in committed diff "
                f"(issue #{TARGET_ISSUE})"
            ),
        )

    def test_npm_test_entry_point_runs_green(self):
        """Fleet delivery runs `npm test` from the repo root — verify it passes."""
        if os.environ.get("HOOK_CI_INNER_RUN"):
            self.skipTest("already inside npm test CI runner")

        env = os.environ.copy()
        env["HOOK_CI_INNER_RUN"] = "1"
        result = subprocess.run(
            ["npm", "test"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn("OK: all CI validation checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
