#!/usr/bin/env python3
import unittest
from agents.claude_review.review_engine import parse_pr_url, generate_review_from_diff

class TestClaudeReviewEngine(unittest.TestCase):
    def test_parse_pr_url_valid(self):
        owner, repo, pr = parse_pr_url("https://github.com/anthropics/claude-code/pull/42")
        self.assertEqual(owner, "anthropics")
        self.assertEqual(repo, "claude-code")
        self.assertEqual(pr, "42")

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://invalid-url.com/something")

    def test_generate_review_structured_output(self):
        sample_diff = """diff --git a/src/auth.py b/src/auth.py
index e69de29..d95f3ad 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -0,0 +1,15 @@
+# Authentication module
+def authenticate(user, password):
+    # TODO: replace with hash check
+    if user == "admin" and password == "secret123":
+        return True
+    return False
+"""
        review = generate_review_from_diff(sample_diff, pr_title="feat: add basic auth module")
        
        self.assertIn("### 📋 Summary of Changes", review)
        self.assertIn("### ⚠️ Identified Risks", review)
        self.assertIn("### 💡 Improvement Suggestions", review)
        self.assertIn("### 🎯 Confidence Score", review)
        self.assertIn("TODO", review)
        self.assertIn("Potential hardcoded credentials", review)

if __name__ == "__main__":
    unittest.main()
