#!/usr/bin/env python3
"""
Unit Test Suite for Structured CHANGELOG Generator.
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "skills" / "changelog-generator"))

import changelog


class TestCommitCategorization(unittest.TestCase):
    """Test mapping of commit prefixes and messages to categories."""

    def test_added_category(self):
        cases = [
            ("feat: implement dark mode", "Added", "implement dark mode"),
            ("feature(ui): add modal dialog", "Added", "**ui:** add modal dialog"),
            ("add user profile settings", "Added", "user profile settings"),
            ("new payment webhook handler", "Added", "payment webhook handler"),
        ]
        for subject, expected_cat, expected_desc in cases:
            with self.subTest(subject=subject):
                cat, desc = changelog.categorize_commit(subject)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(desc, expected_desc)

    def test_fixed_category(self):
        cases = [
            ("fix: resolve null pointer exception", "Fixed", "resolve null pointer exception"),
            ("bug(auth): fix session expiry handling", "Fixed", "**auth:** fix session expiry handling"),
            ("hotfix: patch memory leak in worker", "Fixed", "patch memory leak in worker"),
        ]
        for subject, expected_cat, expected_desc in cases:
            with self.subTest(subject=subject):
                cat, desc = changelog.categorize_commit(subject)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(desc, expected_desc)

    def test_changed_category(self):
        cases = [
            ("refactor: optimize database query builder", "Changed", "optimize database query builder"),
            ("perf: improve page load times", "Changed", "improve page load times"),
            ("chore: update dependencies", "Changed", "update dependencies"),
            ("docs: update API usage guidelines", "Changed", "update API usage guidelines"),
        ]
        for subject, expected_cat, expected_desc in cases:
            with self.subTest(subject=subject):
                cat, desc = changelog.categorize_commit(subject)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(desc, expected_desc)

    def test_removed_category(self):
        cases = [
            ("revert: remove legacy authentication endpoint", "Removed", "remove legacy authentication endpoint"),
            ("delete deprecated config flags", "Removed", "deprecated config flags"),
            ("drop unused table columns", "Removed", "unused table columns"),
        ]
        for subject, expected_cat, expected_desc in cases:
            with self.subTest(subject=subject):
                cat, desc = changelog.categorize_commit(subject)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(desc, expected_desc)


class TestMarkdownGeneration(unittest.TestCase):
    """Test output formatting for CHANGELOG.md."""

    def test_markdown_sections_and_ordering(self):
        mock_commits = [
            {"sha": "1111111", "short_sha": "1111111", "subject": "feat: user dashboard", "author": "Alice", "date": "2026-09-04"},
            {"sha": "2222222", "short_sha": "2222222", "subject": "fix: race condition", "author": "Bob", "date": "2026-09-04"},
            {"sha": "3333333", "short_sha": "3333333", "subject": "refactor: cleanup styles", "author": "Charlie", "date": "2026-09-04"},
            {"sha": "4444444", "short_sha": "4444444", "subject": "revert: rollback bad commit", "author": "Alice", "date": "2026-09-04"},
        ]
        md = changelog.generate_changelog_markdown(mock_commits, version_title="v1.0.0", from_tag="v0.9.0")

        self.assertIn("## [v1.0.0]", md)
        self.assertIn("### Added", md)
        self.assertIn("### Fixed", md)
        self.assertIn("### Changed", md)
        self.assertIn("### Removed", md)
        self.assertIn("`1111111`", md)
        self.assertIn("Alice", md)


if __name__ == "__main__":
    unittest.main()
