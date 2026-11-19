#!/usr/bin/env python3
"""
Unit tests for Claude Code PR Reviewer Agent.
"""

import unittest
from claude_review import analyze_diff, format_review_markdown


class TestClaudeReview(unittest.TestCase):
    def test_clean_diff(self):
        diff = """diff --git a/src/index.js b/src/index.js
index 1234567..89abcdef 100644
--- a/src/index.js
+++ b/src/index.js
@@ -1,3 +1,4 @@
+console.log("hello world");
"""
        analysis = analyze_diff(diff)
        self.assertEqual(len(analysis["files_changed"]), 1)
        self.assertEqual(analysis["additions"], 1)
        self.assertEqual(analysis["deletions"], 0)
        self.assertIn("No critical security or runtime regression risks", analysis["risks"][0])
        self.assertEqual(analysis["confidence"], "High")

    def test_risk_detection(self):
        diff = """diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,2 +1,5 @@
+# TODO: fix security bug
+api_key = "12345-secret"
+eval("user_input()")
+query = "SELECT * FROM users WHERE id = " + user_id
"""
        analysis = analyze_diff(diff)
        risk_text = " ".join(analysis["risks"])
        self.assertIn("TODO", risk_text)
        self.assertIn("credential or secret", risk_text)
        self.assertIn("eval", risk_text)
        self.assertIn("SQL injection", risk_text)

    def test_test_file_suggestion(self):
        diff = """diff --git a/tests/test_basic.py b/tests/test_basic.py
--- a/tests/test_basic.py
+++ b/tests/test_basic.py
@@ -0,0 +1,5 @@
+def test_ok():
+    assert True
"""
        analysis = analyze_diff(diff)
        suggestion_text = " ".join(analysis["suggestions"])
        self.assertIn("Test suite modifications detected", suggestion_text)

    def test_markdown_format_structure(self):
        analysis = {
            "files_changed": ["app.py"],
            "additions": 10,
            "deletions": 2,
            "risks": ["No critical security or runtime regression risks identified from static diff scanning."],
            "suggestions": ["Test suite modifications detected — ensure CI passes across all platform matrix runs."],
            "confidence": "High"
        }
        md = format_review_markdown(analysis, "https://github.com/foo/bar/pull/1")
        self.assertIn("## 🤖 Automated PR Code Review\n\n", md)
        self.assertIn("### 📝 Summary of Changes\n\n", md)
        self.assertIn("### ⚠️ Identified Risks\n\n- No critical security", md)
        self.assertIn("### 💡 Improvement Suggestions\n\n- Test suite modifications", md)
        self.assertIn("### 🎯 Confidence Score: **High**\n", md)


if __name__ == "__main__":
    unittest.main()
