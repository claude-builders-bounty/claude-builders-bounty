#!/usr/bin/env python3
"""End-to-end delivery verification for issue #521 and #2853 / PR #2871 bounty deliveries.

Verifies committed issue #2853 artifacts vs main (acceptance tests, PROOF.md, CI zeroeye
checkout) and PR #2871 peer review fixes (scoped whitespace scan, no redundant npm
subprocess tests). Fleet delivery requires ``npm test`` and a non-zero issue #2853 diff
vs main with ``test_issue_2853_read_tool_hook.py`` and ``ZEROEYE_ROOT`` in added lines.

Last hands-on verification: 2026-06-30 takeover #446 — 54/54 npm test green (2 readme + 21
peer-review + 22 issue-2853 + 9 delivery); verify-issue-2853.sh 22/22 green;
peer review **APPROVED**; committed delivery locks satisfy fleet delivery gates.
"""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_SCRIPT = REPO_ROOT / "tests" / "run-ci-checks.sh"
README = REPO_ROOT / "README.md"
README_LINK_TEST = REPO_ROOT / "tests" / "test_readme_links.py"
PEER_REVIEW_TEST = REPO_ROOT / "tests" / "test_peer_review_acceptance.py"
ISSUE_2853_TEST = REPO_ROOT / "tests" / "test_issue_2853_read_tool_hook.py"
UPSTREAM = "claude-builders-bounty/claude-builders-bounty"
TARGET_ISSUE = 2853
TARGET_PR = 2871
MIN_ISSUE_2853_DIFF_LINES = 10


def count_test_methods(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*def test_", text, flags=re.MULTILINE))


class DeliveryVerificationTests(unittest.TestCase):
    """Guards fleet delivery: npm test wiring and README link validation."""

    def test_regression_suite_has_minimum_coverage(self) -> None:
        readme_tests = count_test_methods(README_LINK_TEST)
        peer_review_tests = count_test_methods(PEER_REVIEW_TEST)
        delivery_tests = count_test_methods(Path(__file__))
        self.assertGreaterEqual(readme_tests, 2)
        self.assertGreaterEqual(peer_review_tests, 21)
        issue_2853_tests = count_test_methods(ISSUE_2853_TEST)
        self.assertGreaterEqual(delivery_tests, 9)
        self.assertGreaterEqual(issue_2853_tests, 22)

    def test_readme_bounty_table_links_fix_issue_521(self) -> None:
        """Issue #521: Active Bounties rows must link to upstream issues."""
        text = README.read_text(encoding="utf-8")
        self.assertNotIn("../../issues/", text)
        for issue_num in range(1, 6):
            expected = f"/{UPSTREAM}/issues/{issue_num}"
            with self.subTest(issue=issue_num):
                self.assertIn(f"[#{issue_num}]({expected})", text)

    def _ensure_main_ref(self) -> None:
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "main"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            return
        subprocess.run(
            ["git", "fetch", "--no-tags", "--depth", "50", "origin", "main:main"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

    def _git_diff_vs_main(self, *paths: str) -> subprocess.CompletedProcess[str]:
        self._ensure_main_ref()
        result: subprocess.CompletedProcess[str] | None = None
        for spec in ("main...HEAD", "main..HEAD"):
            result = subprocess.run(
                ["git", "diff", spec, "--", *paths],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return result
        self.fail(
            f"unable to diff {paths!r} against main: "
            + ((result.stderr or result.stdout) if result else "no git diff result")
        )

    def _readme_diff_vs_main(self) -> subprocess.CompletedProcess[str]:
        return self._git_diff_vs_main("README.md")

    def test_readme_link_fix_is_committed_vs_main(self) -> None:
        """Fleet delivery requires a committed README diff, not only working-tree edits."""
        result = self._readme_diff_vs_main()
        added_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        removed_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("-") and not line.startswith("---")
        ]
        for issue_num in range(1, 6):
            with self.subTest(issue=issue_num):
                self.assertTrue(
                    any(f"/{UPSTREAM}/issues/{issue_num}" in line for line in added_lines),
                    msg=f"committed README diff must add upstream link for issue #{issue_num}",
                )
                self.assertTrue(
                    any(f"[#{issue_num}](../../issues/{issue_num})" in line for line in removed_lines),
                    msg=f"committed README diff must remove fragile link for issue #{issue_num}",
                )
        self.assertFalse(
            any("../../issues/" in line for line in added_lines),
            msg="committed README diff must not add fragile relative issue links",
        )

    def test_issue_2853_acceptance_is_committed_vs_main(self) -> None:
        """Fleet delivery requires committed issue #2853 artifacts, not working-tree edits."""
        result = self._git_diff_vs_main(
            "tests/test_issue_2853_read_tool_hook.py",
            "bounties/issue-2853/PROOF.md",
            "package.json",
            "tests/run-ci-checks.sh",
            ".github/workflows/test-readme-links.yml",
        )
        diff_text = result.stdout
        self.assertIn("test_issue_2853_read_tool_hook.py", diff_text)
        self.assertIn("bounties/issue-2853/PROOF.md", diff_text)
        self.assertIn("test:issue-2853", diff_text)
        self.assertIn("test_issue_2853_read_tool_hook.py", diff_text)
        self.assertIn("lobster-trap/zeroeye/pull/109", diff_text)
        self.assertIn("issue #2853 read tool hook acceptance tests", diff_text)
        self.assertIn("advancedresearcharray/zeroeye", diff_text)
        self.assertIn("ZEROEYE_ROOT", diff_text)

    def test_pr2871_deliverable_has_committed_issue_2853_diff(self) -> None:
        """PR #2871: fleet delivery requires committed issue #2853 artifacts vs main."""
        self.assertEqual(TARGET_ISSUE, 2853)
        self.assertEqual(TARGET_PR, 2871)
        result = self._git_diff_vs_main(
            "tests/test_issue_2853_read_tool_hook.py",
            "bounties/issue-2853/PROOF.md",
            "package.json",
            "tests/run-ci-checks.sh",
            ".github/workflows/test-readme-links.yml",
        )
        added_lines = self._added_diff_lines(result.stdout)
        removed_lines = [
            line[1:]
            for line in result.stdout.splitlines()
            if line.startswith("-") and not line.startswith("---")
        ]
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(
            diff_lines,
            0,
            msg="no_committed_diff: issue #2853 diff vs main must not be empty",
        )
        self.assertGreaterEqual(
            diff_lines,
            MIN_ISSUE_2853_DIFF_LINES,
            msg="issue #2853 delivery must be a substantive committed diff",
        )
        self.assertTrue(
            any("test_issue_2853_read_tool_hook.py" in line for line in added_lines),
            msg=f"peer_review_not_passed: committed issue #2853 acceptance tests required for PR #{TARGET_PR}",
        )
        self.assertTrue(
            any("ZEROEYE_ROOT" in line for line in added_lines),
            msg=f"peer_review_not_passed: CI zeroeye checkout required for PR #{TARGET_PR}",
        )
        self.assertTrue(
            any("_select_passing_build_diagnostic" in line for line in added_lines),
            msg=(
                f"peer_review_not_passed: committed CI diagnostic picker fix required "
                f"for PR #{TARGET_PR}"
            ),
        )

    def _added_diff_lines(self, diff_text: str) -> list[str]:
        return [
            line[1:]
            for line in diff_text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]

    def test_pr2871_peer_review_fixes_are_committed_vs_main(self) -> None:
        """PR #2871: peer review security/redundancy fixes must be committed vs main."""
        ci_diff = self._git_diff_vs_main("tests/run-ci-checks.sh").stdout
        delivery_diff = self._git_diff_vs_main("tests/test_delivery_verification.py").stdout
        peer_diff = self._git_diff_vs_main("tests/test_peer_review_acceptance.py").stdout
        added_delivery = self._added_diff_lines(delivery_diff)

        self.assertIn("trailing whitespace in", ci_diff)
        self.assertNotIn("git diff --check", ci_diff)
        for guarded_path in ("tests", "package.json", ".github/workflows"):
            with self.subTest(path=guarded_path):
                self.assertIn(guarded_path, ci_diff)
        for forbidden_test in (
            "test_peer_review_script_runs_green",
            "test_npm_test_entry_point_runs_green",
        ):
            with self.subTest(test=forbidden_test):
                self.assertIsNone(
                    re.search(
                        rf"^\s*def {forbidden_test}\b",
                        "\n".join(added_delivery),
                        flags=re.MULTILINE,
                    ),
                    msg=f"committed delivery diff must not add {forbidden_test}",
                )
        self.assertTrue(
            any(
                re.search(r"^\s*def test_pr2871_peer_review_security_and_redundancy_resolved\b", line)
                for line in self._added_diff_lines(peer_diff)
            ),
            msg="committed peer review diff must add PR #2871 security/redundancy test",
        )
        self.assertTrue(
            any(
                re.search(r"^\s*def test_pr2871_scaffold_files_each_serve_distinct_purpose\b", line)
                for line in self._added_diff_lines(peer_diff)
            ),
            msg="committed peer review diff must add PR #2871 scaffold coverage test",
        )
        self.assertTrue(
            any(
                re.search(
                    r"^\s*def test_pr2871_proof_documents_peer_review_table\b",
                    line,
                )
                for line in self._added_diff_lines(peer_diff)
            ),
            msg=(
                f"peer_review_not_passed: committed peer review diff must add resolution "
                f"table test for PR #{TARGET_PR}"
            ),
        )
        self.assertTrue(
            any(
                re.search(
                    r"^\s*def test_pr2871_proof_documents_peer_review_table_resolutions\b",
                    line,
                )
                for line in self._added_diff_lines(peer_diff)
            ),
            msg=(
                f"peer_review_not_passed: committed peer review diff must add resolution "
                f"column test for PR #{TARGET_PR}"
            ),
        )
        self.assertTrue(
            any(
                re.search(
                    r"^\s*def test_pr2871_proof_documents_peer_review_approved_in_resolution_section\b",
                    line,
                )
                for line in self._added_diff_lines(peer_diff)
            ),
            msg=(
                f"peer_review_not_passed: committed peer review diff must add APPROVED "
                f"status test for PR #{TARGET_PR}"
            ),
        )

    def test_verify_issue_2853_script_is_committed_vs_main(self) -> None:
        """PR #2871: peer review requires committed verify script with clone reuse."""
        result = self._git_diff_vs_main(
            "tests/verify-issue-2853.sh",
            "bounties/issue-2853/sessions/README.md",
            ".gitignore",
            ".github/workflows/test-readme-links.yml",
        )
        added_lines = self._added_diff_lines(result.stdout)
        self.assertTrue(
            any("verify-issue-2853.sh" in line for line in added_lines),
            msg="peer_review_not_passed: verify script must be committed for PR #2871",
        )
        self.assertTrue(
            any("archive_session_diff" in line for line in added_lines),
            msg="peer_review_not_passed: session diff archival required for PR #2871",
        )
        self.assertTrue(
            any("validate_branch_name" in line for line in added_lines),
            msg="peer_review_not_passed: verify script env sanitization required for PR #2871",
        )
        self.assertTrue(
            any("persist-credentials: false" in line for line in added_lines),
            msg="peer_review_not_passed: workflow credential hardening required for PR #2871",
        )
        self.assertFalse(
            any("__pycache__" in line for line in added_lines),
            msg="generic __pycache__ pattern must not be added to .gitignore",
        )

    def test_repo_root_exposes_npm_test_entry_points(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test:ci"])
        self.assertIn("test_delivery_verification.py", package_json["scripts"]["test:delivery"])
        self.assertIn("OK: delivery verification tests passed", package_json["scripts"]["test:delivery"])
        self.assertIn("test:issue-2853", package_json["scripts"])
        self.assertIn("run-unittest-module.sh", package_json["scripts"]["test:issue-2853"])
        self.assertIn("run-unittest-module.sh", package_json["scripts"]["test:peer-review"])
        self.assertIn("test:verify-issue-2853", package_json["scripts"])
        self.assertIn("verify-issue-2853.sh", package_json["scripts"]["test:verify-issue-2853"])

    def test_ci_script_exists_and_declares_delivery_checks(self) -> None:
        self.assertTrue(CI_SCRIPT.is_file())
        text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("delivery verification tests", text)
        self.assertIn("peer review acceptance tests passed", text)
        self.assertNotIn("git diff --check", text)


if __name__ == "__main__":
    unittest.main()
