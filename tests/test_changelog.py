#!/usr/bin/env python3
"""
Tests for generate-changelog.py
"""

import unittest, tempfile, subprocess, os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "changelog-generator"))
from generate_changelog_lib import categorize, parse_merge, group_commits, generate


class TestCategorize(unittest.TestCase):
    def test_add(self):
        self.assertEqual(categorize("Add new feature"), "Added")
        self.assertEqual(categorize("feat: implement login"), "Added")
    
    def test_fix(self):
        self.assertEqual(categorize("Fix bug in parser"), "Fixed")
        self.assertEqual(categorize("fix: handle null pointer"), "Fixed")
    
    def test_change(self):
        self.assertEqual(categorize("Update README"), "Changed")
        self.assertEqual(categorize("refactor: simplify loop"), "Changed")
    
    def test_remove(self):
        self.assertEqual(categorize("Remove deprecated function"), "Removed")
        self.assertEqual(categorize("drop: old API v1"), "Removed")
    
    def test_default(self):
        self.assertEqual(categorize("some random commit"), "Changed")


class TestParseMerge(unittest.TestCase):
    def test_pr_number(self):
        pr, msg = parse_merge("Merge pull request #42 from branch")
        self.assertEqual(pr, "42")
    
    def test_no_pr(self):
        pr, msg = parse_merge("Merge branch develop")
        self.assertIsNone(pr)


class TestGroupCommits(unittest.TestCase):
    def test_basic_grouping(self):
        commits = [
            {"message": "Add new login", "hash": "abc123", "short_hash": "abc", "author": "dev", "date": "2026-01-01"},
            {"message": "Fix crash on startup", "hash": "def456", "short_hash": "def", "author": "dev", "date": "2026-01-02"},
            {"message": "Update docs", "hash": "gh789", "short_hash": "ghi", "author": "dev", "date": "2026-01-03"},
        ]
        cats = group_commits(commits)
        self.assertIn("Added", cats)
        self.assertIn("Fixed", cats)
        self.assertEqual(len(cats["Added"]), 1)
        self.assertEqual(len(cats["Fixed"]), 1)


class TestIntegration(unittest.TestCase):
    def test_on_real_repo(self):
        # Test on this repo
        repo = Path(__file__).parent.parent.parent
        result = subprocess.run(
            [sys.executable, "changelog-generator/generate-changelog.py", "--repo", ".", "--output", "/dev/null"],
            capture_output=True, text=True, cwd=repo
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Found", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
