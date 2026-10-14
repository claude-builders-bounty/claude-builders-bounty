#!/usr/bin/env python3
"""
Automated Unit Tests for Claude Code PR Reviewer
Verifies:
1. URL parsing (owner, repo, PR number).
2. Risk detection (SQL injection, hardcoded secrets, missing tests, silent exceptions).
3. Confidence score calculation.
4. Markdown formatting compliance with acceptance criteria.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from claude_review import parse_pr_url, analyze_diff, format_markdown_review

class TestClaudeReview(unittest.TestCase):

    def test_parse_pr_url(self):
        owner, repo, num = parse_pr_url("https://github.com/facebook/react/pull/12345")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(num, 12345)

        with self.assertRaises(ValueError):
            parse_pr_url("https://invalid-url.com/something")

    def test_diff_with_secrets_and_sql(self):
        diff = """
diff --git a/app/db.py b/app/db.py
--- a/app/db.py
+++ b/app/db.py
@@ -1,5 +1,6 @@
+API_KEY = "sk-live-1234567890abcdef"
+def run_query(table):
+    cursor.execute("DROP TABLE " + table)
"""
        meta = {"title": "Add DB drop handler", "number": 10}
        res = analyze_diff(diff, meta=meta)

        self.assertIn("Hardcoded credentials or API tokens detected", "".join(res["risks"]))
        self.assertIn("Irreversible database mutations", "".join(res["risks"]))
        self.assertIn("Missing automated test coverage", "".join(res["risks"]))
        self.assertEqual(res["confidence"], "Low")

    def test_clean_diff_with_tests(self):
        diff = """
diff --git a/src/math.py b/src/math.py
--- a/src/math.py
+++ b/src/math.py
@@ -1,2 +1,3 @@
+def add(a, b): return a + b
diff --git a/tests/test_math.py b/tests/test_math.py
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -1,2 +1,3 @@
+def test_add(): assert add(1, 2) == 3
"""
        meta = {"title": "Implement safe add utility", "number": 20}
        res = analyze_diff(diff, meta=meta)

        self.assertEqual(res["confidence"], "High")
        self.assertTrue(len(res["suggestions"]) > 0)

    def test_markdown_formatting_structure(self):
        res = {
            "summary": "This PR adds mathematical additions across 2 files.",
            "risks": ["No critical risks detected."],
            "suggestions": ["Run continuous integration."],
            "confidence": "High"
        }
        md = format_markdown_review(res, pr_url="https://github.com/owner/repo/pull/1")

        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("**Confidence Score:**", md)
        self.assertIn("🟢 **High**", md)

if __name__ == "__main__":
    unittest.main()
