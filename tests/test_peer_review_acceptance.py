#!/usr/bin/env python3
"""Peer-review acceptance cases for issue #521 README bounty table links."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
UPSTREAM = "claude-builders-bounty/claude-builders-bounty"
BOUNTY_TABLE_RE = re.compile(
    r"## Active Bounties\s*\n\n(.*?)(?:\n---|\Z)",
    re.DOTALL,
)
ISSUE_LINK_RE = re.compile(r"\[#(\d+)\]\(([^)]+)\)")


class PeerReviewAcceptanceTests(unittest.TestCase):
    """Maps issue #521 acceptance criteria to repo artifacts and link behavior."""

    EXPECTED_ISSUES = ("1", "2", "3", "4", "5")

    def test_readme_bounty_table_has_five_upstream_issue_links(self):
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")

        links = dict(ISSUE_LINK_RE.findall(table_match.group(1)))
        self.assertEqual(set(links), set(self.EXPECTED_ISSUES))

        for issue_num in self.EXPECTED_ISSUES:
            expected = f"/{UPSTREAM}/issues/{issue_num}"
            with self.subTest(issue=issue_num):
                self.assertEqual(links[issue_num], expected)

    def test_readme_has_no_fragile_relative_issue_links(self):
        text = README.read_text(encoding="utf-8")
        self.assertNotIn("../../issues/", text)
        self.assertNotRegex(text, r"\]\(issues/\d+\)")

    def test_readme_bounty_section_documents_absolute_paths(self):
        text = README.read_text(encoding="utf-8")
        section_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(section_match, "Active Bounties section not found in README")
        self.assertIn("absolute `/owner/repo/issues/N` paths", section_match.group(1))
        self.assertIn("forks and blob views", section_match.group(1))

    def test_regression_test_module_exists(self):
        regression = REPO_ROOT / "tests/test_readme_links.py"
        self.assertTrue(regression.is_file())
        text = regression.read_text(encoding="utf-8")
        self.assertIn("test_bounty_table_links_point_to_upstream_issues", text)
        self.assertIn("test_readme_has_no_escaping_issue_links", text)

    def test_ci_workflow_runs_unified_validation(self):
        workflow = REPO_ROOT / ".github/workflows/test-readme-links.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("run-ci-checks.sh", text)
        self.assertIn("tests/test_readme_links.py", text)

    def test_makefile_exposes_test_and_ci_validate(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test:", makefile)
        self.assertIn("ci-validate:", makefile)
        self.assertIn("run-ci-checks.sh", makefile)

    def test_repo_root_exposes_npm_test_entry_point(self):
        package_json = (REPO_ROOT / "package.json").read_text(encoding="utf-8")
        self.assertIn('"test"', package_json)
        self.assertIn("run-ci-checks.sh", package_json)
        self.assertIn('"test:readme-links"', package_json)
        self.assertIn('"test:peer-review"', package_json)
        self.assertIn("OK: peer review acceptance tests passed", package_json)

    def test_makefile_exposes_peer_review_target(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test-peer-review:", makefile)
        self.assertIn("test:peer-review", makefile)

    def test_run_ci_checks_script_exists_and_is_executable(self):
        script = REPO_ROOT / "tests/run-ci-checks.sh"
        self.assertTrue(script.is_file())
        self.assertTrue(script.stat().st_mode & 0o111)

    def test_run_ci_checks_guards_attribution_and_peer_review(self):
        script = (REPO_ROOT / "tests/run-ci-checks.sh").read_text(encoding="utf-8")
        self.assertIn("peer review acceptance tests passed", script)
        self.assertIn("test_delivery_verification.py", script)
        self.assertIn("git log -1 --format='%B'", script)
        self.assertIn("Ran ${readme_link_tests} README link tests — OK", script)
        self.assertIn("Ran ${peer_review_tests} peer review acceptance tests — OK", script)
        self.assertIn("Forbidden agent attribution trailer found in HEAD commit message", script)


if __name__ == "__main__":
    unittest.main()
