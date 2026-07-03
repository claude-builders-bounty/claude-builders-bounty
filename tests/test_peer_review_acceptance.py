#!/usr/bin/env python3
"""Peer-review acceptance cases for issue #2746 README bounty table links."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def tests_dir() -> Path:
    return Path(__file__).resolve().parent


README = repo_root() / "README.md"
UPSTREAM = "claude-builders-bounty/claude-builders-bounty"
TARGET_ISSUE = 2746
TARGET_PR = 2846
BOUNTY_TABLE_RE = re.compile(
    r"## Active Bounties\s*\n\n(.*?)(?:\n---|\Z)",
    re.DOTALL,
)
ISSUE_LINK_RE = re.compile(r"\[#(\d+)\]\(([^)]+)\)")


class PeerReviewAcceptanceTests(unittest.TestCase):
    """Maps issue #2746 acceptance criteria to README link behavior."""

    EXPECTED_ISSUES = ("1", "2", "3", "4", "5")

    def test_peer_review_targets_issue_2746_pr_2846(self) -> None:
        self.assertEqual(TARGET_ISSUE, 2746)
        self.assertEqual(TARGET_PR, 2846)

    def test_readme_bounty_table_has_five_upstream_issue_links(self) -> None:
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")

        links = dict(ISSUE_LINK_RE.findall(table_match.group(1)))
        self.assertEqual(set(links), set(self.EXPECTED_ISSUES))

        for issue_num in self.EXPECTED_ISSUES:
            expected = f"/{UPSTREAM}/issues/{issue_num}"
            with self.subTest(issue=issue_num):
                self.assertEqual(links[issue_num], expected)

    def test_readme_has_no_fragile_relative_issue_links(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertNotIn("../../issues/", text)
        self.assertNotRegex(text, r"\]\(issues/\d+\)")

    def test_bounty_issue_hrefs_are_root_absolute_for_pr_2846(self) -> None:
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")
        for issue_num, href in ISSUE_LINK_RE.findall(table_match.group(1)):
            with self.subTest(issue=issue_num, href=href):
                self.assertTrue(href.startswith("/"), f"Issue #{issue_num} href must be root-absolute")
                self.assertNotIn("..", href)
                self.assertFalse(href.startswith("issues/"))

    def test_readme_bounty_section_documents_absolute_paths(self) -> None:
        text = README.read_text(encoding="utf-8")
        section_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(section_match, "Active Bounties section not found in README")
        section = section_match.group(1)
        self.assertIn("absolute `/owner/repo/issues/N` paths", section)
        self.assertIn("forks and blob views", section)
        self.assertIn(UPSTREAM, text)

    def test_regression_test_module_exists(self) -> None:
        matches = sorted(tests_dir().glob("test_*readme*.py"))
        self.assertTrue(matches, "expected a readme link regression test module")
        text = matches[0].read_text(encoding="utf-8")
        self.assertIn("test_bounty_table_links_point_to_upstream_issues", text)
        self.assertIn("test_readme_has_no_escaping_issue_links", text)

    def test_ci_workflow_runs_unified_validation(self) -> None:
        workflow = repo_root() / ".github" / "workflows" / "test-readme-links.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("run-ci-checks.sh", text)
        self.assertIn("tests/test_readme_links.py", text)

    def test_ci_workflow_fetches_full_git_history(self) -> None:
        workflow = repo_root() / ".github" / "workflows" / "test-readme-links.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)

    def test_repo_root_exposes_npm_test_entry_point(self) -> None:
        package_json = (repo_root() / "package.json").read_text(encoding="utf-8")
        self.assertIn('"test"', package_json)
        self.assertIn("run-ci-checks.sh", package_json)
        self.assertIn('"test:readme-links"', package_json)
        self.assertIn('"test:peer-review"', package_json)
        self.assertIn('"test:delivery"', package_json)

    def test_run_ci_checks_script_exists(self) -> None:
        script = tests_dir() / "run-ci-checks.sh"
        self.assertTrue(script.is_file())

    def test_run_ci_checks_guards_attribution_and_delivery(self) -> None:
        script = (tests_dir() / "run-ci-checks.sh").read_text(encoding="utf-8")
        self.assertIn("peer review acceptance tests passed", script)
        self.assertIn("test_delivery_verification.py", script)
        self.assertIn("delivery verification tests passed", script)
        self.assertIn("git log -1 --format='%B'", script)
        self.assertIn("sensitive", script.lower())


if __name__ == "__main__":
    unittest.main()
