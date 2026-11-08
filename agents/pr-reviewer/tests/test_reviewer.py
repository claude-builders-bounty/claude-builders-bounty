import unittest
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from reviewer import parse_pr_url, analyze_diff, generate_review_markdown


class TestPRReviewerAgent(unittest.TestCase):
    def test_parse_pr_url(self):
        owner, repo, num = parse_pr_url("https://github.com/facebook/react/pull/12345")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(num, 12345)

        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/invalid/url")

    def test_analyze_diff_clean(self):
        clean_diff = """diff --git a/src/math.py b/src/math.py
--- a/src/math.py
+++ b/src/math.py
@@ -1,3 +1,4 @@
 def add(a, b):
     return a + b
+def multiply(a, b): return a * b
diff --git a/tests/test_math.py b/tests/test_math.py
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -1,3 +1,4 @@
+def test_multiply(): assert multiply(2, 3) == 6
"""
        analysis = analyze_diff(clean_diff)
        self.assertEqual(len(analysis["files_changed"]), 2)
        self.assertEqual(len(analysis["risks"]), 0)
        self.assertEqual(analysis["confidence"], "High")

    def test_analyze_diff_detects_risks(self):
        risky_diff = """diff --git a/db/wipe.py b/db/wipe.py
--- a/db/wipe.py
+++ b/db/wipe.py
@@ -0,0 +1,4 @@
+import os
+os.system("rm -rf /tmp/data")
+api_key = "ghp_123456789012345678901234567890123456"
+cors()
"""
        analysis = analyze_diff(risky_diff)
        self.assertTrue(len(analysis["risks"]) >= 2)
        risk_text = " ".join(analysis["risks"])
        self.assertIn("Destructive Command", risk_text)
        self.assertIn("Hardcoded Secret", risk_text)

    def test_generate_review_markdown_structure(self):
        sample_analysis = {
            "files_changed": ["src/auth.js", "tests/auth.test.js"],
            "additions": 45,
            "deletions": 12,
            "risks": [],
            "suggestions": ["Ensure JWT expiration is tested."],
            "confidence": "High"
        }
        md = generate_review_markdown(sample_analysis, pr_url="https://github.com/foo/bar/pull/1")
        self.assertIn("## 🤖 Automated PR Review", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score", md)
        self.assertIn("**High**", md)


if __name__ == "__main__":
    unittest.main()
