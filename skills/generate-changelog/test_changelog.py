#!/usr/bin/env python3
"""
Unit tests for generate_changelog.py categorizer and markdown generator.
"""

import unittest
from generate_changelog import categorize_commit, build_changelog_markdown

class TestChangelogGenerator(unittest.TestCase):
    def test_conventional_commits(self):
        cat, desc = categorize_commit("feat(auth): add JWT token refresh endpoint")
        self.assertEqual(cat, "Added")
        self.assertIn("**auth**: Add JWT token refresh endpoint", desc)

        cat, desc = categorize_commit("fix(router): prevent race condition in slot reservation")
        self.assertEqual(cat, "Fixed")
        self.assertIn("**router**: Prevent race condition in slot reservation", desc)

        cat, desc = categorize_commit("refactor(gateway): migrate proxy handler to async pipeline")
        self.assertEqual(cat, "Changed")
        self.assertIn("**gateway**: Migrate proxy handler to async pipeline", desc)

        cat, desc = categorize_commit("remove(legacy): delete deprecated v1 token endpoint")
        self.assertEqual(cat, "Removed")
        self.assertIn("**legacy**: Delete deprecated v1 token endpoint", desc)

        cat, desc = categorize_commit("chore(deps): bump certifi from 2024.2.2 to 2024.8.30")
        self.assertEqual(cat, "Maintenance")
        self.assertIn("**deps**: Bump certifi from 2024.2.2 to 2024.8.30", desc)

    def test_non_conventional_commit_fallback(self):
        cat, desc = categorize_commit("Add support for Solana Native AMM token swap")
        self.assertEqual(cat, "Added")

        cat, desc = categorize_commit("Fix overflow when calculating basis point fees")
        self.assertEqual(cat, "Fixed")

        cat, desc = categorize_commit("Remove unused mock test artifacts")
        self.assertEqual(cat, "Removed")

    def test_markdown_structure(self):
        categories = {
            "Added": [{"hash": "a1b2c3d", "desc": "New feature", "author": "dev", "date": "2026-10-27"}],
            "Fixed": [{"hash": "e5f6g7h", "desc": "Fixed bug", "author": "dev", "date": "2026-10-27"}],
            "Changed": [],
            "Removed": [],
            "Maintenance": []
        }
        md = build_changelog_markdown(categories, version="v1.0.0", date_str="2026-10-27")
        self.assertIn("## [v1.0.0] - 2026-10-27", md)
        self.assertIn("### Added", md)
        self.assertIn("- New feature ([`a1b2c3d`])", md)
        self.assertIn("### Fixed", md)
        self.assertIn("- Fixed bug ([`e5f6g7h`])", md)
        self.assertNotIn("### Changed", md)

if __name__ == "__main__":
    unittest.main()
