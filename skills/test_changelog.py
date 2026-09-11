#!/usr/bin/env python3
"""
Unit Test Suite for Structured Changelog Generator
Validates commit parsing, conventional categorization, and Keep-A-Changelog Markdown formatting.
"""

import unittest
import os
import tempfile
from generate_changelog import categorize_commits, build_changelog_markdown, update_changelog_file

class TestChangelogGenerator(unittest.TestCase):
    def test_categorization_conventional_commits(self):
        sample_commits = [
            {"hash": "a1b2c3d", "author": "Alice", "message": "feat(auth): Add OAuth2 Google login"},
            {"hash": "e4f5g6h", "author": "Bob", "message": "fix(db): Resolve connection pool leak"},
            {"hash": "i7j8k9l", "author": "Charlie", "message": "refactor(api): Optimize JSON serializer"},
            {"hash": "m0n1o2p", "author": "Dave", "message": "remove(legacy): Drop deprecated v1 endpoints"},
            {"hash": "q3r4s5t", "author": "Eve", "message": "perf: Increase cache TTL to 3600s"}
        ]

        categories = categorize_commits(sample_commits)

        self.assertEqual(len(categories["Added"]), 1)
        self.assertIn("**auth**: Add OAuth2 Google login", categories["Added"][0])

        self.assertEqual(len(categories["Fixed"]), 1)
        self.assertIn("**db**: Resolve connection pool leak", categories["Fixed"][0])

        self.assertEqual(len(categories["Changed"]), 2) # refactor + perf
        self.assertEqual(len(categories["Removed"]), 1)
        self.assertIn("Drop deprecated v1 endpoints", categories["Removed"][0])

    def test_build_markdown(self):
        categories = {
            "Added": ["Feature A ([`1234567`])"],
            "Fixed": ["Bug B ([`7654321`])"],
            "Changed": [],
            "Removed": []
        }

        md = build_changelog_markdown(categories, version="v1.2.0", release_date="2026-09-12")

        self.assertIn("## [v1.2.0] - 2026-09-12", md)
        self.assertIn("### Added", md)
        self.assertIn("- Feature A ([`1234567`])", md)
        self.assertIn("### Fixed", md)
        self.assertIn("- Bug B ([`7654321`])", md)
        self.assertNotIn("### Changed", md)

    def test_update_changelog_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "CHANGELOG.md")

            section1 = "## [v1.0.0] - 2026-01-01\n\n### Added\n- Initial release\n"
            update_changelog_file(section1, file_path)

            section2 = "## [v1.1.0] - 2026-02-01\n\n### Added\n- Feature X\n"
            content = update_changelog_file(section2, file_path)

            self.assertTrue(os.path.exists(file_path))
            self.assertIn("# Changelog", content)
            self.assertIn("## [v1.1.0]", content)
            self.assertIn("## [v1.0.0]", content)

if __name__ == "__main__":
    unittest.main()
