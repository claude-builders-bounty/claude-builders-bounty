#!/usr/bin/env python3
"""
Unit tests for Changelog Generator
Tests commit categorization, conventional commit parsing, tag detection, and Keep a Changelog Markdown output.
"""

import unittest
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent))
from changelog import categorize_commit, generate_changelog_content

class TestChangelogGenerator(unittest.TestCase):
    def test_categorize_added(self):
        cases = [
            ("a1b2c3d feat(auth): add OAuth2 login support", "Added", "Add OAuth2 login support"),
            ("e5f6g7h feature: add dark mode theme", "Added", "Add dark mode theme"),
            ("1234567 implement webhooks retry policy", "Added", "Implement webhooks retry policy"),
            ("9876543 create new analytics dashboard", "Added", "Create new analytics dashboard")
        ]
        for commit, expected_cat, expected_msg in cases:
            with self.subTest(commit=commit):
                cat, c_hash, msg = categorize_commit(commit)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(msg, expected_msg)

    def test_categorize_fixed(self):
        cases = [
            ("3344556 fix(api): resolve memory leak on websocket reconnect", "Fixed", "Resolve memory leak on websocket reconnect"),
            ("7788990 bugfix: handle null pointer in user profile", "Fixed", "Handle null pointer in user profile"),
            ("aabbccd patch: correct pagination offset", "Fixed", "Correct pagination offset"),
            ("ddeeff0 resolves #42 connection timeout", "Fixed", "Resolves #42 connection timeout")
        ]
        for commit, expected_cat, expected_msg in cases:
            with self.subTest(commit=commit):
                cat, c_hash, msg = categorize_commit(commit)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(msg, expected_msg)

    def test_categorize_removed(self):
        cases = [
            ("1122334 remove legacy v1 REST API", "Removed", "Remove legacy v1 REST API"),
            ("4455667 deprecate MD5 password hashing", "Removed", "Deprecate MD5 password hashing"),
            ("889900a delete unused utility modules", "Removed", "Delete unused utility modules")
        ]
        for commit, expected_cat, expected_msg in cases:
            with self.subTest(commit=commit):
                cat, c_hash, msg = categorize_commit(commit)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(msg, expected_msg)

    def test_categorize_changed(self):
        cases = [
            ("99aabbc refactor(db): migrate to drizzle orm", "Changed", "Migrate to drizzle orm"),
            ("ddeeff1 perf: optimize query indexing", "Changed", "Optimize query indexing"),
            ("2233445 docs: update installation guide in README", "Changed", "Update installation guide in README"),
            ("6677889 chore: bump dependencies", "Changed", "Bump dependencies")
        ]
        for commit, expected_cat, expected_msg in cases:
            with self.subTest(commit=commit):
                cat, c_hash, msg = categorize_commit(commit)
                self.assertEqual(cat, expected_cat)
                self.assertEqual(msg, expected_msg)

    def test_generate_changelog_content_structure(self):
        categories = {
            "Added": ["Add OAuth2 login (`a1b2c3d`)"],
            "Fixed": ["Resolve websocket leak (`3344556`)"],
            "Changed": ["Migrate to drizzle ORM (`99aabbc`)"],
            "Removed": ["Remove legacy API (`1122334`)"]
        }
        output = generate_changelog_content("v1.0.0", categories, "v0.9.0")
        
        self.assertIn("## [v1.0.0]", output)
        self.assertIn("(since v0.9.0)", output)
        self.assertIn("### Added", output)
        self.assertIn("- Add OAuth2 login (`a1b2c3d`)", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Changed", output)
        self.assertIn("### Removed", output)

if __name__ == "__main__":
    unittest.main()
