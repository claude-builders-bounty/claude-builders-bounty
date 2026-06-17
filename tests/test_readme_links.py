#!/usr/bin/env python3
"""Regression tests for README bounty table issue links (issue #521).

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
    def test_readme_has_no_escaping_issue_links(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertNotIn(
            "../../issues/",
            text,
            "README must not use ../../issues/ links that resolve per-fork",
        )

    def test_bounty_table_links_point_to_upstream_issues(self) -> None:
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
                self.assertTrue(
                    href.startswith("/"),
                    f"Issue #{issue_num} link {href!r} must be an absolute path",
                )
                self.assertEqual(
                    href,
                    expected,
                    f"Issue #{issue_num} should link to upstream {expected}",
                )


if __name__ == "__main__":
    unittest.main()
