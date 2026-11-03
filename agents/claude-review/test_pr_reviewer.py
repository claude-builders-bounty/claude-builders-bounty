#!/usr/bin/env python3
"""
Unit Test Suite for Claude Code PR Reviewer Sub-Agent
"""

import unittest
from claude_review import parse_pr_url, analyze_diff, format_review_markdown

class TestPRReviewer(unittest.TestCase):
    def test_parse_pr_url(self):
        owner, repo, pr = parse_pr_url("https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5007")
        self.assertEqual(owner, "claude-builders-bounty")
        self.assertEqual(repo, "claude-builders-bounty")
        self.assertEqual(pr, 5007)

    def test_analyze_diff_risk_detection(self):
        pr_data = {
            "title": "feat: test destructive changes",
            "changed_files": 2,
            "additions": 10,
            "deletions": 0,
            "base": {"repo": {"language": "Python"}}
        }
        diff_text = "+++ b/schema.sql\n+ DROP TABLE users;\n+ DELETE FROM accounts;"
        analysis = analyze_diff(pr_data, diff_text)

        self.assertIn("summary", analysis)
        self.assertIn("risks", analysis)
        self.assertIn("suggestions", analysis)
        self.assertIn(analysis["confidence"], ["Low", "Medium", "High"])

        # Check that destructive SQL was detected
        has_sql_risk = any("destructive SQL" in r for r in analysis["risks"])
        self.assertTrue(has_sql_risk, "Expected destructive SQL risk to be identified")

    def test_format_review_markdown(self):
        analysis = {
            "summary": "This is a concise 2-sentence summary. It explains the feature.",
            "risks": ["Risk of unhandled timeout", "Dependency change"],
            "suggestions": ["Add unit tests", "Consider caching"],
            "confidence": "High"
        }
        md = format_review_markdown(analysis)

        self.assertIn("## 🤖 Automated Code Review (Claude Sub-Agent)", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score", md)
        self.assertIn("**High**", md)

if __name__ == "__main__":
    unittest.main()
