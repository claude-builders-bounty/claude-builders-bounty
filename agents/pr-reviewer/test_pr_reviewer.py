#!/usr/bin/env python3
"""
Comprehensive Test suite for Claude Code PR Reviewer CLI & Agent.
"""

import unittest
import tempfile
from pathlib import Path
from claude_review import parse_pr_url, analyze_diff, format_review_markdown

class TestPRReviewer(unittest.TestCase):
    def test_parse_pr_url_valid(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/facebook/react/pull/12345")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(pr_num, 12345)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://gitlab.com/owner/repo/pull/123")
        with self.assertRaises(ValueError):
            parse_pr_url("not-a-url")

    def test_analyze_diff_destructive_risk_detection(self):
        sample_diff = """diff --git a/script.sh b/script.sh
index 123..456 100644
--- a/script.sh
+++ b/script.sh
@@ -1,3 +1,4 @@
+rm -rf /data/cache
"""
        res = analyze_diff(sample_diff, "test", "repo", 1)
        self.assertTrue(any("destructive" in r.lower() for r in res["risks"]))

    def test_analyze_diff_credential_exposure_detection(self):
        sample_diff = """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
+api_key = "secret12345"
"""
        res = analyze_diff(sample_diff, "test", "repo", 2)
        self.assertTrue(any("credential" in r.lower() for r in res["risks"]))

    def test_confidence_scoring(self):
        # Small diff with test -> High
        diff_small_with_test = """diff --git a/test_app.py b/test_app.py
--- a/test_app.py
+++ b/test_app.py
@@ -0,0 +1,10 @@
+def test_ok(): pass
"""
        res_high = analyze_diff(diff_small_with_test, "org", "proj", 3)
        self.assertEqual(res_high["confidence"], "High")

    def test_format_review_markdown(self):
        data = {
            "summary": "Sample summary text.",
            "risks": ["Risk 1"],
            "suggestions": ["Suggestion 1"],
            "confidence": "High",
            "files_count": 1,
            "additions": 10,
            "deletions": 2
        }
        md = format_review_markdown(data, "https://github.com/test/repo/pull/1")
        self.assertIn("## 🤖 Claude Code PR Review", md)
        self.assertIn("Sample summary text.", md)
        self.assertIn("Risk 1", md)
        self.assertIn("Suggestion 1", md)
        self.assertIn("**High**", md)

if __name__ == "__main__":
    unittest.main()
