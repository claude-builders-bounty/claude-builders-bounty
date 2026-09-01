import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import unittest
from unittest.mock import patch, MagicMock
from claude_review import parse_pr_url, analyze_diff, format_markdown_review

class TestClaudeReviewerAgent(unittest.TestCase):

    def test_parse_pr_url_valid(self):
        url = "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4055"
        owner, repo, pr_num = parse_pr_url(url)
        self.assertEqual(owner, "claude-builders-bounty")
        self.assertEqual(repo, "claude-builders-bounty")
        self.assertEqual(pr_num, 4055)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/invalid/url")

    def test_analyze_diff_risk_detection(self):
        mock_pr_data = {
            "title": "feat: add unsafe script",
            "body": "PR description",
            "changed_files": 2,
            "additions": 45,
            "deletions": 5,
            "user": {"login": "dev_user"}
        }
        mock_diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,6 @@
+api_key = "sk-live-secret-test-token-key-12345"
+os.system("rm -rf /tmp")
+query = "SELECT * FROM users WHERE name = " + user_input
"""
        analysis = analyze_diff(mock_pr_data, mock_diff)
        self.assertEqual(analysis["title"], "feat: add unsafe script")
        self.assertTrue(any("Secret" in r for r in analysis["risks"]))
        self.assertTrue(any("Arbitrary Code" in r for r in analysis["risks"]))
        self.assertTrue(any("SQL Injection" in r for r in analysis["risks"]))
        self.assertIn("Confidence Score", format_markdown_review(analysis))

    def test_format_markdown_review_structure(self):
        analysis = {
            "title": "Safe PR",
            "author": "author",
            "files_modified": ["main.py"],
            "additions": 10,
            "deletions": 2,
            "summary": "This is a clean change summary.",
            "risks": ["No critical security or regression risks identified in the diff."],
            "suggestions": ["Ensure CI checks pass."],
            "confidence": "High"
        }
        md = format_markdown_review(analysis)
        self.assertIn("## 🤖 Claude Code PR Review", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score: **High**", md)

if __name__ == "__main__":
    unittest.main()
