#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Claude Code PR Reviewer Agent
============================================
Tests URL parsing, diff analysis heuristics, risk detection, and markdown formatting.
"""

import unittest
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

import claude_review

class TestPRReviewer(unittest.TestCase):
    def test_parse_pr_url(self):
        url = "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4930"
        owner, repo, pr_num = claude_review.parse_pr_url(url)
        self.assertEqual(owner, "claude-builders-bounty")
        self.assertEqual(repo, "claude-builders-bounty")
        self.assertEqual(pr_num, 4930)

    def test_risk_detection(self):
        pr_meta = {
            "title": "feat: test PR",
            "user": {"login": "testuser"},
            "changed_files": 2,
            "additions": 50,
            "deletions": 5
        }
        # Diff containing a suspicious token
        diff_text = """
+ API_KEY = "ghp_1234567890abcdef1234567890abcdef"
+ DROP TABLE secret_records;
        """
        analysis = claude_review.analyze_diff(pr_meta, diff_text)
        self.assertTrue(any("sensitive API token" in r for r in analysis["risks"]))
        self.assertTrue(any("Destructive file or SQL" in r for r in analysis["risks"]))

    def test_format_review_markdown(self):
        analysis = {
            "summary": "This is a clean test summary for verification.",
            "risks": ["Risk item A"],
            "suggestions": ["Suggestion item B"],
            "confidence": "High",
            "title": "Clean PR",
            "author": "dev"
        }
        md = claude_review.format_review_markdown(analysis)
        self.assertIn("## 🤖 Claude Code Automated PR Review", md)
        self.assertIn("### 📋 Summary of Changes", md)
        self.assertIn("Risk item A", md)
        self.assertIn("Suggestion item B", md)
        self.assertIn("Confidence Score: **High**", md)

if __name__ == "__main__":
    unittest.main()
