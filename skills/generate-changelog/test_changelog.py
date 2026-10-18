#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Generate Changelog Skill
==================================
Tests git commit categorization, markdown formatting, and file generation.
"""

import unittest
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

import changelog

class TestChangelogGenerator(unittest.TestCase):
    def test_categorization(self):
        sample_commits = [
            {"hash": "a1b2c3d", "message": "feat(auth): add OAuth2 token refresh support"},
            {"hash": "e4f5g6h", "message": "fix: resolve memory leak in worker thread"},
            {"hash": "i7j8k9l", "message": "refactor: simplify database connection pool"},
            {"hash": "m0n1o2p", "message": "remove: legacy v1 REST endpoint"},
            {"hash": "q3r4s5t", "message": "chore: bump dependencies to latest"}
        ]
        
        cats = changelog.categorize_commits(sample_commits)
        self.assertEqual(len(cats["Added"]), 1)
        self.assertIn("add OAuth2 token refresh support", cats["Added"][0][1])
        
        self.assertEqual(len(cats["Fixed"]), 1)
        self.assertIn("resolve memory leak in worker thread", cats["Fixed"][0][1])
        
        self.assertEqual(len(cats["Changed"]), 2)
        self.assertEqual(len(cats["Removed"]), 1)

    def test_markdown_builder(self):
        categories = {
            "Added": [("1234567", "Brand new visual UI component")],
            "Fixed": [("890abcd", "Fix null pointer in config parser")],
            "Changed": [],
            "Removed": []
        }
        md = changelog.build_changelog_markdown(categories, version="v1.2.0", date_str="2026-10-18")
        self.assertIn("## [v1.2.0] - 2026-10-18", md)
        self.assertIn("### Added", md)
        self.assertIn("Brand new visual UI component (`1234567`)", md)
        self.assertIn("### Fixed", md)
        self.assertIn("Fix null pointer in config parser (`890abcd`)", md)

if __name__ == "__main__":
    unittest.main()
