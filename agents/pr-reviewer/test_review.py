#!/usr/bin/env python3
"""
Unit tests for Claude Code PR Reviewer Agent
Tests URL parsing, diff analysis, risk signal detection, and Markdown formatting.
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from claude_review import parse_pr_url, analyze_diff, format_review_markdown

class TestPRReviewer(unittest.TestCase):
    def test_parse_pr_url(self):
        url = "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4301"
        owner, repo, num = parse_pr_url(url)
        self.assertEqual(owner, "claude-builders-bounty")
        self.assertEqual(repo, "claude-builders-bounty")
        self.assertEqual(num, 4301)

    def test_parse_invalid_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://example.com/not-a-pr")

    def test_analyze_diff_risk_detection(self):
        mock_meta = {
            "title": "feat: add user authentication",
            "changed_files": 2,
            "additions": 45,
            "deletions": 5,
            "number": 101,
            "user": {"login": "octocat"}
        }
        mock_diff = """
diff --git a/src/auth.ts b/src/auth.ts
index 1234..5678 100644
--- a/src/auth.ts
+++ b/src/auth.ts
@@ -1,3 +1,6 @@
+const API_SECRET = "sk_live_1234567890abcdef123456";
+async function authenticate() {
+  const res = await fetch("https://api.example.com");
+}
"""
        analysis = analyze_diff(mock_meta, mock_diff)
        
        # Should flag hardcoded secret and unhandled async
        self.assertTrue(any("credential or API secret" in r for r in analysis["risks"]))
        self.assertTrue(any("Asynchronous operations" in r for r in analysis["risks"]))
        self.assertEqual(analysis["pr_number"], 101)

    def test_format_review_markdown(self):
        analysis = {
            "summary": "This pull request adds user authentication. Overall structure is clean.",
            "risks": ["No critical security or architectural blockers identified in this diff."],
            "suggestions": ["Ensure unit test coverage for new endpoints."],
            "confidence": "High",
            "pr_title": "feat: auth",
            "pr_number": 101,
            "author": "octocat"
        }
        md = format_review_markdown(analysis)
        self.assertIn("## 🤖 Claude Code PR Review", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### 🔍 Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("**Confidence Score**: **High**", md)

if __name__ == "__main__":
    unittest.main()
