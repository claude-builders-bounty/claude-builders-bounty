#!/usr/bin/env python3
"""Tests for generate_changelog.py"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent to path and import directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import generate_changelog as gc_mod

# Use the functions directly
classify_commit = gc_mod.classify_commit
group_commits = gc_mod.group_commits
format_changelog = gc_mod.format_changelog


class TestClassifyCommit(unittest.TestCase):
    def test_feat_added(self):
        raw_type, cat = classify_commit("feat: add user login", "")
        self.assertEqual(raw_type, "feat")
        self.assertEqual(cat, "Added")

    def test_feat_with_scope(self):
        raw_type, cat = classify_commit("feat(auth): implement OAuth2 flow", "")
        self.assertEqual(raw_type, "feat")
        self.assertEqual(cat, "Added")

    def test_fix(self):
        raw_type, cat = classify_commit("fix: resolve memory leak", "")
        self.assertEqual(cat, "Fixed")

    def test_breaking_change(self):
        raw_type, cat = classify_commit("feat!: drop Python 3.7 support", "")
        self.assertEqual(cat, "Added")
        self.assertEqual(raw_type, "feat")

    def test_keyword_fallback_add(self):
        raw_type, cat = classify_commit("Adding new search feature", "")
        self.assertEqual(cat, "Added")

    def test_keyword_fallback_bug(self):
        raw_type, cat = classify_commit("Bug fix in parser module", "")
        self.assertEqual(cat, "Fixed")

    def test_docs(self):
        raw_type, cat = classify_commit("docs: update README with examples", "")
        self.assertEqual(cat, "Documentation")

    def test_deprecated(self):
        raw_type, cat = classify_commit("deprecate: old API endpoint", "")
        self.assertEqual(cat, "Deprecated")

    def test_security(self):
        raw_type, cat = classify_commit("security: fix XSS vulnerability", "")
        self.assertEqual(cat, "Security")

    def test_unknown_falls_to_changed(self):
        raw_type, cat = classify_commit("random message with no keywords", "")
        self.assertEqual(cat, "Changed")


class TestGroupCommits(unittest.TestCase):
    def test_groups_in_order(self):
        commits = [
            {"category": "Fixed", "sha": "1", "subject": "fix"},
            {"category": "Added", "sha": "2", "subject": "feat"},
            {"category": "Changed", "sha": "3", "subject": "refactor"},
        ]
        groups = group_commits(commits)
        keys = list(groups.keys())
        self.assertEqual(keys[0], "Added")
        self.assertEqual(keys[1], "Fixed")
        self.assertEqual(keys[2], "Changed")

    def test_empty_groups_skipped(self):
        commits = [
            {"category": "Added", "sha": "1", "subject": "feat"},
        ]
        groups = group_commits(commits)
        self.assertIn("Added", groups)
        self.assertNotIn("Fixed", groups)


class TestFormatChangelog(unittest.TestCase):
    def test_empty_commits(self):
        result = format_changelog([], "https://github.com/test/repo", "v1.0.0")
        self.assertIn("Changelog", result)
        self.assertIn("v1.0.0", result)
        self.assertIn("No significant changes", result)

    def test_formats_categories(self):
        commits = [
            {"sha": "abc1234", "date": "", "author": "Alice",
             "subject": "feat: add user auth", "body": "", "raw_type": "feat", "category": "Added"},
            {"sha": "def5678", "date": "", "author": "Bob",
             "subject": "fix: fix login bug", "body": "", "raw_type": "fix", "category": "Fixed"},
        ]
        result = format_changelog(commits, "https://github.com/test/repo", "v1.0.0")
        self.assertIn("✨ Added", result)
        self.assertIn("🐛 Fixed", result)
        self.assertIn("abc1234", result)
        self.assertIn("def5678", result)
        self.assertIn("2 commits", result)

    def test_no_repo_url(self):
        commits = [
            {"sha": "abc1234", "date": "", "author": "Alice",
             "subject": "feat: something", "body": "", "raw_type": "feat", "category": "Added"},
        ]
        result = format_changelog(commits)
        self.assertIn("abc1234", result)


if __name__ == "__main__":
    unittest.main()
