#!/usr/bin/env python3
"""
Comprehensive Test suite for generate_changelog.py
Validates category classification, tag range inspection, Keep a Changelog formatting, and empty commit handling.
"""

import unittest
from generate_changelog import categorize_commit, build_changelog

class TestGenerateChangelog(unittest.TestCase):
    def test_categorize_commit(self):
        self.assertEqual(categorize_commit("feat(auth): add OAuth2 provider login")[0], "Added")
        self.assertEqual(categorize_commit("fix(db): resolve connection pool leak on timeout")[0], "Fixed")
        self.assertEqual(categorize_commit("refactor(core): optimize vector similarity query")[0], "Changed")
        self.assertEqual(categorize_commit("remove(legacy): drop deprecated v1 REST endpoints")[0], "Removed")
        self.assertEqual(categorize_commit("chore: update dependencies")[0], "Changed")

    def test_changelog_builder_formatting(self):
        commits = [
            ("a1b2c3d", "Alice", "feat(api): add webhooks support"),
            ("e5f6g7h", "Bob", "fix(ui): prevent modal flicker on rerender"),
            ("i9j0k1l", "Charlie", "remove(cache): drop redis v5 fallback")
        ]
        output = build_changelog("v1.2.0", "v1.1.0", commits)
        self.assertIn("## [v1.2.0]", output)
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Removed", output)
        self.assertIn("Add webhooks support ([`a1b2c3d`] - Alice)", output)
        self.assertIn("Prevent modal flicker on rerender ([`e5f6g7h`] - Bob)", output)

    def test_empty_commits(self):
        output = build_changelog("v1.0.0", None, [])
        self.assertIn("No qualifying commits recorded", output)

if __name__ == "__main__":
    unittest.main()
