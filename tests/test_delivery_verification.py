#!/usr/bin/env python3
"""End-to-end delivery verification for issue #521 README bounty link fix."""

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

    def test_readme_link_fix_is_committed_vs_main(self) -> None:
        """Fleet delivery requires a committed README diff, not only working-tree edits."""
        result = subprocess.run(
            ["git", "diff", "main...HEAD", "--", "README.md"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
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
        self.assertTrue(
            any(f"/{UPSTREAM}/issues/1" in line for line in added_lines),
            msg="committed README diff must add upstream issue links",
        )
        self.assertTrue(
            any("../../issues/1" in line for line in removed_lines),
            msg="committed README diff must remove fragile relative issue links",
        )
        self.assertFalse(
            any("../../issues/" in line for line in added_lines),
            msg="committed README diff must not add fragile relative issue links",
        )

    def test_repo_root_exposes_npm_test_entry_points(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test:ci"])

    def test_ci_script_exists_and_declares_delivery_checks(self) -> None:
        self.assertTrue(CI_SCRIPT.is_file())
        text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("delivery verification tests", text)
        self.assertIn("peer review acceptance tests passed", text)

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


if __name__ == "__main__":
    unittest.main()
