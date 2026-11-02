#!/usr/bin/env python3
"""
Unit tests for Claude Code PR Review Sub-Agent
"""

import unittest
from claude_review import PRReviewAgent

class TestPRReviewAgent(unittest.TestCase):
    def setUp(self):
        self.agent = PRReviewAgent(token="dummy_token")

    def test_parse_pr_url_valid(self):
        url = "https://github.com/facebook/react/pull/28000"
        owner, repo, number = self.agent.parse_pr_url(url)
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(number, 28000)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            self.agent.parse_pr_url("https://github.com/facebook/react/issues/28000")

    def test_analyze_diff_risk_heuristics(self):
        fake_pr = {
            "title": "Add payments module",
            "body": "PR description",
            "author": "dev",
            "base_branch": "main",
            "head_branch": "feature",
            "additions": 450,
            "deletions": 10,
            "changed_files_count": 2,
            "files": [
                {"filename": "src/payment.py"},
                {"filename": "package.json"}
            ],
            "raw_diff": 'api_key = "sk_live_1234567890abcdef123456"\neval("cmd")',
            "html_url": "https://github.com/test/repo/pull/1"
        }
        analysis = self.agent.analyze_diff(fake_pr)
        
        # Check risks detected
        risk_text = " ".join(analysis["risks"])
        self.assertIn("Security", risk_text)
        self.assertIn("Dependency Updates", risk_text)
        self.assertIn("Test Coverage", risk_text)
        self.assertEqual(analysis["confidence"], "Low")

    def test_format_markdown_structure(self):
        fake_pr = {
            "title": "Fix typo in documentation",
            "author": "contributor",
            "base_branch": "main",
            "additions": 5,
            "deletions": 2,
            "files": [{"filename": "docs/guide.md"}],
            "raw_diff": "- typo\n+ fixed typo",
            "html_url": "https://github.com/test/repo/pull/2"
        }
        analysis = self.agent.analyze_diff(fake_pr)
        md = self.agent.format_markdown(analysis, fake_pr)

        self.assertIn("## 🤖 Claude Code PR Review", md)
        self.assertIn("### 📋 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score:", md)

if __name__ == "__main__":
    unittest.main()
