#!/usr/bin/env python3
import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from claude_review import parse_pr_url, analyze_diff, format_markdown_review

class TestClaudeReview(unittest.TestCase):

    def test_parse_pr_url(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr_num, 123)

        with self.assertRaises(ValueError):
            parse_pr_url("https://invalid-url.com/something")

    def test_analyze_diff_structure(self):
        sample_diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
+API_KEY = "sk-live-1234567890abcdef"
+eval("2 + 2")
"""
        res = analyze_diff(sample_diff, pr_url="https://github.com/test/repo/pull/1")
        self.assertIn("summary", res)
        self.assertIn("risks", res)
        self.assertIn("suggestions", res)
        self.assertIn("confidence", res)
        self.assertTrue(any("credential" in r.lower() for r in res["risks"]))
        self.assertTrue(any("eval" in r.lower() for r in res["risks"]))

    def test_empty_diff_handling(self):
        res = analyze_diff("")
        self.assertEqual(res["confidence"], "High")
        self.assertIn("empty", res["summary"].lower())

    def test_format_markdown_review(self):
        data = {
            "summary": "This modifies 1 file.",
            "risks": ["Test risk."],
            "suggestions": ["Test suggestion."],
            "confidence": "Medium"
        }
        md = format_markdown_review(data, pr_url="https://github.com/owner/repo/pull/42")
        self.assertIn("Summary of Changes", md)
        self.assertIn("Identified Risks", md)
        self.assertIn("Improvement Suggestions", md)
        self.assertIn("Confidence Score", md)
        self.assertIn("Medium", md)

if __name__ == "__main__":
    unittest.main()
