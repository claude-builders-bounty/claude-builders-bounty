#!/usr/bin/env python3
"""Regression tests for README bounty table issue links (issue #521 / PR #2532).

Bounty rows must use absolute /owner/repo/issues/N hrefs so links resolve on
forks and blob views; fragile ../../issues/N paths escape the repo root.
"""

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


class ReadmeLinkTests(unittest.TestCase):
    """Regression coverage for README issue link href conventions."""

    def test_readme_issue_links_use_upstream_hrefs_only(self) -> None:
        """Every /issues/ href in README must use the upstream absolute path prefix."""
        text = README.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
            href = match.group(1)
            if "/issues/" not in href:
                continue
            with self.subTest(href=href):
                self.assertTrue(
                    href.startswith(f"/{UPSTREAM}/issues/"),
                    f"issue link href {href!r} must be absolute upstream path",
                )

    def test_readme_has_no_escaping_issue_links(self) -> None:
        """README must not contain fragile ../../issues/ relative hrefs."""
        text = README.read_text(encoding="utf-8")
        self.assertNotIn(
            "../../issues/",
            text,
            "README must not use ../../issues/ links that resolve per-fork",
        )

    def test_bounty_section_note_links_issue_521(self) -> None:
        """Active Bounties contributor note must link issue #521 with upstream path."""
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")
        self.assertIn(
            f"[issue #521](/{UPSTREAM}/issues/521)",
            table_match.group(1),
        )

    def test_bounty_table_links_point_to_upstream_issues(self) -> None:
        """Each bounty table row (#1–#5) must link to the canonical upstream issue."""
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")

        matches = ISSUE_LINK_RE.findall(table_match.group(1))
        self.assertEqual(len(matches), 5, "expected exactly 5 bounty table issue links")

        for issue_num, href in matches:
            expected = f"/{UPSTREAM}/issues/{issue_num}"
            with self.subTest(issue=issue_num, href=href):
                self.assertFalse(
                    href.startswith("../"),
                    f"Issue #{issue_num} link {href!r} uses fragile relative paths",
                )
                self.assertFalse(
                    href.startswith("issues/"),
                    f"Issue #{issue_num} link {href!r} resolves to repo files on blob views",
                )
                self.assertEqual(
                    href,
                    expected,
                    f"Issue #{issue_num} should link to upstream {expected}",
                )

    def test_readme_bounty_table_links_fix_issue_521(self) -> None:
        """Issue #521: Active Bounties rows must link to upstream issues."""
        text = README.read_text(encoding="utf-8")
        self.assertNotIn("../../issues/", text)
        for issue_num in range(1, 6):
            expected = f"/{UPSTREAM}/issues/{issue_num}"
            with self.subTest(issue=issue_num):
                self.assertIn(f"[#{issue_num}]({expected})", text)

    def test_bounty_links_resolve_on_forked_repo_context(self) -> None:
        """Absolute upstream hrefs must still target canonical issues after fork/merge."""
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")

        for issue_num, href in ISSUE_LINK_RE.findall(table_match.group(1)):
            with self.subTest(issue=issue_num, href=href):
                self.assertTrue(
                    href.startswith("/"),
                    f"Issue #{issue_num} href {href!r} must be root-absolute on forks",
                )
                self.assertNotIn(
                    "github.com",
                    href,
                    f"Issue #{issue_num} href {href!r} must use repo-root paths, not full URLs",
                )
                self.assertRegex(
                    href,
                    rf"^/{UPSTREAM}/issues/\d+$",
                    f"Issue #{issue_num} href {href!r} must match upstream issue path",
                )

    def test_bounty_links_reject_invalid_href_patterns(self) -> None:
        """README must not use bare, relative, or blob-view issue href patterns."""
        text = README.read_text(encoding="utf-8")
        invalid_patterns = (
            r"\]\(\.\./\.\./issues/\d+\)",
            r"\]\(issues/\d+\)",
            r"\]\(blob/.+/issues/\d+\)",
        )
        for pattern in invalid_patterns:
            with self.subTest(pattern=pattern):
                self.assertNotRegex(
                    text,
                    pattern,
                    f"README contains invalid issue link pattern: {pattern}",
                )

    def test_new_bounty_rows_must_use_upstream_hrefs(self) -> None:
        """Any new bounty table row must use the same upstream absolute href convention."""
        text = README.read_text(encoding="utf-8")
        table_match = BOUNTY_TABLE_RE.search(text)
        self.assertIsNotNone(table_match, "Active Bounties section not found in README")

        table_rows = [
            line
            for line in table_match.group(1).splitlines()
            if line.strip().startswith("| [#")
        ]
        self.assertGreaterEqual(len(table_rows), 5, "expected at least five bounty rows")

        for row in table_rows:
            with self.subTest(row=row.strip()):
                self.assertRegex(
                    row,
                    rf"\[#\d+\]\(/{UPSTREAM}/issues/\d+\)",
                    f"bounty row {row.strip()!r} must use upstream absolute issue href",
                )


if __name__ == "__main__":
    unittest.main()
