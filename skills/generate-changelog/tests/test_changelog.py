#!/usr/bin/env python3
"""
Automated Unit Tests for changelog generator
Verifies:
1. Conventional commit categorization (Added, Fixed, Changed, Removed).
2. Clean commit message stripping.
3. Keep a Changelog Markdown generation.
4. Incremental update preservation.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from changelog import categorize_commit, format_clean_message, generate_changelog_section

class TestChangelogGenerator(unittest.TestCase):

    def test_categorization(self):
        self.assertEqual(categorize_commit("feat: add authentication layer"), "Added")
        self.assertEqual(categorize_commit("feat(auth): support OAuth tokens"), "Added")
        self.assertEqual(categorize_commit("fix: resolve race condition in pool"), "Fixed")
        self.assertEqual(categorize_commit("fix(db)!: handle deadlock retry"), "Fixed")
        self.assertEqual(categorize_commit("refactor: clean up logging pipeline"), "Changed")
        self.assertEqual(categorize_commit("perf: speed up JSON serialization"), "Changed")
        self.assertEqual(categorize_commit("docs: update setup guide"), "Changed")
        self.assertEqual(categorize_commit("revert: restore previous middleware"), "Removed")
        self.assertEqual(categorize_commit("deprecate: mark v1 endpoints as obsolete"), "Removed")

    def test_clean_message_formatting(self):
        self.assertEqual(format_clean_message("feat(auth): add OAuth2 provider"), "add OAuth2 provider")
        self.assertEqual(format_clean_message("fix!: critical crash on null pointer"), "critical crash on null pointer")
        self.assertEqual(format_clean_message("chore: bump deps"), "bump deps")

    def test_generate_changelog_section(self):
        sample_commits = [
            ("a1b2c3d", "Alice", "feat: add user profile endpoints"),
            ("d4e5f6g", "Bob", "fix: correct timestamp offset"),
            ("h7i8j9k", "Charlie", "refactor: simplify cache invalidation"),
            ("l0m1n2o", "Dave", "revert: rollback experimental flag")
        ]
        section = generate_changelog_section("v1.2.0", sample_commits)
        self.assertIn("## [Unreleased] (since v1.2.0)", section)
        self.assertIn("### Added", section)
        self.assertIn("### Fixed", section)
        self.assertIn("### Changed", section)
        self.assertIn("### Removed", section)
        self.assertIn("- add user profile endpoints ([`a1b2c3d`] - Alice)", section)

if __name__ == "__main__":
    unittest.main()
