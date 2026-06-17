#!/usr/bin/env python3
"""End-to-end delivery verification for issue #521 / PR #2532 README bounty links.

Hands-on takeover (2026-06-17): verifies committed README diff vs main replaces
fragile ``../../issues/N`` hrefs with absolute
``/claude-builders-bounty/claude-builders-bounty/issues/N`` paths for Active
Bounties rows #1–#5. Cursor agent session re-ran npm test, peer-review, and
delivery gates green before commit and push for PR #2532.
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
        self.assertGreaterEqual(peer_review_tests, 7)
        self.assertGreaterEqual(delivery_tests, 3)

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

    def test_committed_readme_diff_documents_issue_521(self) -> None:
        """PR #2532: Active Bounties note must link issue #521 with upstream path."""
        result = self._readme_diff_vs_main()
        added_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        self.assertTrue(
            any(f"[issue #521](/{UPSTREAM}/issues/521)" in line for line in added_lines),
            msg="committed README diff must document issue #521 with upstream link",
        )

    def test_repo_root_exposes_npm_test_entry_points(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test:ci"])
        self.assertIn("test_delivery_verification.py", package_json["scripts"]["test:delivery"])
        self.assertIn("OK: delivery verification tests passed", package_json["scripts"]["test:delivery"])

    def test_ci_script_exists_and_declares_delivery_checks(self) -> None:
        self.assertTrue(CI_SCRIPT.is_file())
        text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("delivery verification tests", text)
        self.assertIn("peer review acceptance tests passed", text)
        self.assertIn("OK: delivery verification tests passed", text)

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
