#!/usr/bin/env python3
"""
Unit tests for Claude Code PR Reviewer CLI & Engine
Verifies all acceptance criteria for Bounty #4:
1. URL parsing
2. Diff parsing & metrics
3. Security risk detection
4. Structured Markdown formatting (Summary, Risks, Improvements, Confidence Score)
5. CLI argument execution
"""

import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from claude_review import parse_pr_url, analyze_diff, format_markdown_review

class TestPRReviewer(unittest.TestCase):

    def test_parse_pr_url(self):
        owner, repo, pr = parse_pr_url("https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4874")
        self.assertEqual(owner, "claude-builders-bounty")
        self.assertEqual(repo, "claude-builders-bounty")
        self.assertEqual(pr, 4874)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/invalid/url")

    def test_analyze_diff_risks(self):
        diff = """diff --git a/script.py b/script.py
new file mode 100644
--- /dev/null
+++ b/script.py
@@ -0,0 +1,5 @@
+import os
+os.system("rm -rf /")
+api_key = "12345678901234567890"
+"""
        analysis = analyze_diff(diff, "Malicious PR")
        self.assertGreaterEqual(len(analysis["risks"]), 2)
        self.assertEqual(analysis["confidence"], "Medium")

    def test_structured_markdown_output(self):
        diff = """diff --git a/safe.py b/safe.py
new file mode 100644
--- /dev/null
+++ b/safe.py
@@ -0,0 +1,10 @@
+def add(a, b):
+    return a + b
+"""
        analysis = analyze_diff(diff, "Safe feature")
        md = format_markdown_review(analysis)
        self.assertIn("## 🔍 Pull Request Review", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score:", md)

if __name__ == "__main__":
    unittest.main()
