#!/usr/bin/env python3
"""
Unit tests for Structured CHANGELOG Generator.
"""

import unittest
from generate_changelog import categorize_commits, build_markdown


class TestChangelogGenerator(unittest.TestCase):
    def test_categorization(self):
        sample_commits = [
            "feat(auth): add OAuth2 PKCE login support",
            "fix(db): resolve connection pool starvation",
            "refactor(api): clean up response serializer",
            "remove: deprecated legacy v1 endpoints",
            "chore: update dependencies",
        ]
        cats = categorize_commits(sample_commits)
        self.assertEqual(len(cats["Added"]), 1)
        self.assertIn("add OAuth2 PKCE login support", cats["Added"][0])

        self.assertEqual(len(cats["Fixed"]), 1)
        self.assertIn("resolve connection pool starvation", cats["Fixed"][0])

        self.assertEqual(len(cats["Removed"]), 1)
        self.assertIn("deprecated legacy v1 endpoints", cats["Removed"][0])

        self.assertEqual(len(cats["Changed"]), 2)

    def test_markdown_structure(self):
        cats = {
            "Added": ["New feature A"],
            "Fixed": ["Bug fix B"],
            "Changed": ["Refactored C"],
            "Removed": ["Removed D"],
        }
        md = build_markdown(cats)
        self.assertIn("# Changelog", md)
        self.assertIn("### Added", md)
        self.assertIn("- New feature A", md)
        self.assertIn("### Fixed", md)
        self.assertIn("- Bug fix B", md)
        self.assertIn("### Changed", md)
        self.assertIn("### Removed", md)


if __name__ == "__main__":
    unittest.main()
