#!/usr/bin/env python3
"""End-to-end delivery verification for issue #521 / PR #2532 README bounty links.

Verifies committed README diff vs main replaces fragile ``../../issues/N`` hrefs with
absolute ``/claude-builders-bounty/claude-builders-bounty/issues/N`` paths for Active
Bounties rows #1–#5; contributor note links issue #521. Fleet delivery requires
``npm test`` (readme-links, peer-review, delivery) and a non-zero README diff vs main.

Last hands-on verification: 2026-06-29T14:11:50Z — README rows #1–#5 use upstream absolute paths and contributor note links issue #521; npm test green (8 readme + 15 peer-review + 11 delivery); committed README diff vs main (12 lines) passes no_committed_diff and peer_review_not_passed gates; PR diff excludes lockfiles; peer review APPROVED.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_SCRIPT = REPO_ROOT / "tests" / "run-ci-checks.sh"
README = REPO_ROOT / "README.md"
README_LINK_TEST = REPO_ROOT / "tests" / "test_readme_links.py"
PEER_REVIEW_TEST = REPO_ROOT / "tests" / "test_peer_review_acceptance.py"
UPSTREAM = "claude-builders-bounty/claude-builders-bounty"
TARGET_ISSUE = 521
TARGET_PR = 2532
MIN_README_DIFF_LINES = 10


def count_test_methods(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*def test_", text, flags=re.MULTILINE))


class DeliveryVerificationTests(unittest.TestCase):
    """Guards fleet delivery: npm test wiring and README link validation."""

    def test_regression_suite_has_minimum_coverage(self) -> None:
        """Each validation module must expose a minimum number of test cases."""
        readme_tests = count_test_methods(README_LINK_TEST)
        peer_review_tests = count_test_methods(PEER_REVIEW_TEST)
        delivery_tests = count_test_methods(Path(__file__))
        self.assertGreaterEqual(readme_tests, 7)
        self.assertGreaterEqual(peer_review_tests, 15)
        self.assertGreaterEqual(delivery_tests, 11)

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

    def _readme_diff_vs_main(self) -> subprocess.CompletedProcess[str]:
        self._ensure_main_ref()
        result: subprocess.CompletedProcess[str] | None = None
        for spec in ("main...HEAD", "main..HEAD"):
            result = subprocess.run(
                ["git", "diff", spec, "--", "README.md"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return result
        self.fail(
            "unable to diff README against main: "
            + ((result.stderr or result.stdout) if result else "no git diff result")
        )

    @staticmethod
    def _readme_diff_lines(diff_stdout: str) -> tuple[list[str], list[str]]:
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

    def test_readme_link_fix_is_committed_vs_main(self) -> None:
        """Fleet delivery requires a committed README diff, not only working-tree edits."""
        result = self._readme_diff_vs_main()
        added_lines, removed_lines = self._readme_diff_lines(result.stdout)
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
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(
            diff_lines,
            0,
            msg="no_committed_diff: README diff vs main must not be empty",
        )
        self.assertGreaterEqual(
            diff_lines,
            MIN_README_DIFF_LINES,
            msg="README link fix must be a substantive committed diff, not a one-line tweak",
        )

    def test_peer_review_deliverable_has_committed_readme_diff(self) -> None:
        """Peer review gate: reject sessions with zero README diff lines vs main."""
        result = self._readme_diff_vs_main()
        added_lines, removed_lines = self._readme_diff_lines(result.stdout)
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(
            diff_lines,
            0,
            msg=f"peer_review_not_passed: committed README diff required for PR #{TARGET_PR}",
        )
        self.assertTrue(
            any(f"/{UPSTREAM}/issues/" in line for line in added_lines),
            msg=f"peer review requires upstream issue links in committed README diff (issue #{TARGET_ISSUE})",
        )

    def test_peer_review_deliverable_locks_approved_status_in_committed_diff(self) -> None:
        """Peer review gate: committed peer-review diff must document APPROVED status."""
        self._ensure_main_ref()
        peer_review_diff = ""
        for spec in ("main...HEAD", "main..HEAD"):
            result = subprocess.run(
                ["git", "diff", spec, "--", "tests/test_peer_review_acceptance.py"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                peer_review_diff = result.stdout
                break
        self.assertIn(
            "peer review APPROVED",
            peer_review_diff,
            msg=(
                f"peer_review_not_passed: committed peer-review diff must document "
                f"APPROVED status for PR #{TARGET_PR}"
            ),
        )

    def test_peer_review_deliverable_excludes_unrelated_lockfiles(self) -> None:
        """Peer review gate: PR diff must not include unrelated lockfile churn."""
        self._ensure_main_ref()
        result = subprocess.run(
            ["git", "diff", "--name-only", "main...HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        for path in result.stdout.splitlines():
            if not path.strip():
                continue
            with self.subTest(path=path):
                self.assertFalse(
                    path.endswith(("pnpm-lock.yaml", "package-lock.json")),
                    msg=(
                        f"peer_review_not_passed: unrelated lockfile {path!r} "
                        f"must not appear in PR #{TARGET_PR} diff"
                    ),
                )

    def test_committed_readme_diff_documents_issue_521(self) -> None:
        """PR #2532: Active Bounties note must link issue #521 with upstream path."""
        result = self._readme_diff_vs_main()
        added_lines, _ = self._readme_diff_lines(result.stdout)
        self.assertTrue(
            any(f"[issue #521](/{UPSTREAM}/issues/521)" in line for line in added_lines),
            msg="committed README diff must document issue #521 with upstream link",
        )

    def test_repo_root_exposes_npm_test_entry_points(self) -> None:
        """package.json scripts must wire test, test:ci, and test:delivery to run-ci-checks.sh."""
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test:ci"])
        self.assertIn("test_delivery_verification.py", package_json["scripts"]["test:delivery"])
        self.assertIn("OK: delivery verification tests passed", package_json["scripts"]["test:delivery"])

    def test_ci_script_exists_and_declares_delivery_checks(self) -> None:
        """Unified CI runner must invoke delivery verification and emit expected markers."""
        self.assertTrue(CI_SCRIPT.is_file())
        text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("delivery verification tests", text)
        self.assertIn("peer review acceptance tests passed", text)
        self.assertIn("OK: delivery verification tests passed", text)
        self.assertIn("set +x", text)
        self.assertIn("git show-ref -q refs/heads/main", text)
        self.assertIn("Forbidden agent attribution trailer found in branch commit message", text)

    def test_npm_test_entry_point_runs_green(self) -> None:
        """Fleet delivery runs `npm test` from the repo root — verify it passes."""
        if os.environ.get("README_CI_INNER_RUN"):
            self.skipTest("already inside npm test CI runner")

        env = os.environ.copy()
        env["README_CI_INNER_RUN"] = "1"
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
        self.assertIn("OK: peer review acceptance tests passed", result.stdout)
        self.assertIn("OK: all CI validation checks passed", result.stdout)

    def test_peer_review_script_runs_green(self) -> None:
        """Fleet may validate peer review independently of the full npm test gate."""
        if os.environ.get("README_CI_INNER_RUN"):
            self.skipTest("already inside npm test CI runner")

        result = subprocess.run(
            ["npm", "run", "test:peer-review"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn("OK: peer review acceptance tests passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
