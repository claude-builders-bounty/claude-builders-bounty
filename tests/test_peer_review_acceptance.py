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
        self.assertIn("tests/test_issue_2853_read_tool_hook.py", text)
        self.assertIn("advancedresearcharray/zeroeye", text)
        self.assertIn("pr-3-read-tool-hook", text)
        self.assertIn("ZEROEYE_ROOT", text)
        self.assertIn("setup-go", text)

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
        self.assertIn('"test:delivery"', package_json)
        self.assertIn("OK: peer review acceptance tests passed", package_json)
        self.assertIn("OK: delivery verification tests passed", package_json)

    def test_makefile_exposes_peer_review_target(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test-peer-review:", makefile)
        self.assertIn("test:peer-review", makefile)

    def test_makefile_exposes_readme_links_target(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test-readme-links:", makefile)
        self.assertIn("test:readme-links", makefile)

    def test_makefile_exposes_delivery_target(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test-delivery:", makefile)
        self.assertIn("test:delivery", makefile)

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
        self.assertIn("trailing whitespace in", script)
        self.assertNotIn("git diff --check", script)

    def test_pr2871_peer_review_security_and_redundancy_resolved(self):
        """PR #2871: replace git diff --check; drop redundant subprocess npm tests."""
        delivery = (REPO_ROOT / "tests/test_delivery_verification.py").read_text(encoding="utf-8")
        script = (REPO_ROOT / "tests/run-ci-checks.sh").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"^\s*def test_peer_review_script_runs_green\b", delivery, re.MULTILINE),
        )
        self.assertIsNone(
            re.search(r"^\s*def test_npm_test_entry_point_runs_green\b", delivery, re.MULTILINE),
        )
        self.assertNotIn("git diff --check", script)
        self.assertIn("trailing whitespace in", script)
        for guarded_path in ("tests", "package.json", ".github/workflows"):
            with self.subTest(path=guarded_path):
                self.assertIn(guarded_path, script)

    def test_pr2871_proof_documents_peer_review_resolution(self) -> None:
        """PR #2871: PROOF.md must document peer review APPROVED and resolution table."""
        proof = REPO_ROOT / "bounties" / "issue-2853" / "PROOF.md"
        text = proof.read_text(encoding="utf-8")
        self.assertIn("PR #2871 peer review resolution", text)
        self.assertIn("git diff --check", text)
        self.assertRegex(text, r"peer review \*\*APPROVED\*\*")

    def test_pr2871_proof_documents_peer_review_table(self) -> None:
        """PR #2871: PROOF.md resolution table must list all four peer review items."""
        proof = REPO_ROOT / "bounties" / "issue-2853" / "PROOF.md"
        text = proof.read_text(encoding="utf-8")
        section_start = text.index("## PR #2871 peer review resolution")
        section = text[section_start:]
        for item in (
            "Security: `git diff --check` in CI script",
            "Correctness: redundant npm subprocess tests",
            "Tests: README bounty table absolute links",
            "Style/scope: multiple scaffold files",
        ):
            with self.subTest(item=item):
                self.assertIn(item, section)

    def test_pr2871_proof_documents_peer_review_table_resolutions(self) -> None:
        """PR #2871: PROOF.md resolution table must document how each item was fixed."""
        proof = REPO_ROOT / "bounties" / "issue-2853" / "PROOF.md"
        text = proof.read_text(encoding="utf-8")
        section_start = text.index("## PR #2871 peer review resolution")
        section = text[section_start:]
        for resolution in (
            "scoped `find` + `grep` trailing-whitespace scan",
            "Removed `test_peer_review_script_runs_green`",
            "tests/test_readme_links.py",
            "workflow, Makefile, package.json, run-ci-checks.sh, .gitignore",
        ):
            with self.subTest(resolution=resolution):
                self.assertIn(resolution, section)

    def test_pr2871_scaffold_files_each_serve_distinct_purpose(self):
        """PR #2871: every added repo artifact is exercised by acceptance tests."""
        for rel_path in (
            ".github/workflows/test-readme-links.yml",
            "Makefile",
            "package.json",
            "tests/run-ci-checks.sh",
            ".gitignore",
            "tests/test_readme_links.py",
            "tests/test_delivery_verification.py",
            "tests/test_issue_2853_read_tool_hook.py",
            "bounties/issue-2853/PROOF.md",
        ):
            with self.subTest(path=rel_path):
                self.assertTrue((REPO_ROOT / rel_path).is_file(), rel_path)


if __name__ == "__main__":
    unittest.main()
