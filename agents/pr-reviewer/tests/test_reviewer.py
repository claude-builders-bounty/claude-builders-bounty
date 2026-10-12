import unittest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from claude_review import parse_pr_url, analyze_diff_heuristics, format_review_markdown

class TestPRReviewer(unittest.TestCase):

    def test_parse_pr_url_valid(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/foo-org/bar-repo/pull/42")
        self.assertEqual(owner, "foo-org")
        self.assertEqual(repo, "bar-repo")
        self.assertEqual(pr_num, 42)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/foo-org/bar-repo/issues/42")

    def test_analyze_clean_diff(self):
        sample_diff = """diff --git a/src/math.py b/src/math.py
index 1111..2222 100644
--- a/src/math.py
+++ b/src/math.py
@@ -1,3 +1,5 @@
+def add(a: int, b: int) -> int:
+    return a + b
diff --git a/tests/test_math.py b/tests/test_math.py
index 3333..4444 100644
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -1,3 +1,5 @@
+def test_add():
+    assert add(1, 2) == 3
"""
        analysis = analyze_diff_heuristics(sample_diff)
        self.assertIn("additions", analysis)
        self.assertEqual(analysis["files_count"], 2)
        self.assertEqual(analysis["confidence"], "High")
        self.assertTrue(len(analysis["summary"]) > 20)

    def test_detect_dangerous_command(self):
        sample_diff = """diff --git a/scripts/clean.sh b/scripts/clean.sh
--- a/scripts/clean.sh
+++ b/scripts/clean.sh
@@ -1,1 +1,2 @@
+rm -rf /tmp/build_cache
"""
        analysis = analyze_diff_heuristics(sample_diff)
        self.assertEqual(analysis["confidence"], "Low")
        has_rm_risk = any("rm -rf" in r for r in analysis["risks"])
        self.assertTrue(has_rm_risk)

    def test_detect_secret_leak(self):
        sample_diff = """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,1 +1,2 @@
+API_KEY = "sk-live-secret-1234567890abcdef12345"
"""
        analysis = analyze_diff_heuristics(sample_diff)
        self.assertEqual(analysis["confidence"], "Low")
        has_secret_risk = any("Security Warning" in r for r in analysis["risks"])
        self.assertTrue(has_secret_risk)

    def test_format_markdown_sections(self):
        analysis = {
            "summary": "This PR updates 1 file with 10 additions.",
            "risks": ["No tests modified"],
            "suggestions": ["Add unit tests"],
            "confidence": "Medium",
            "confidence_reason": "Standard diff check",
            "files_count": 1,
            "additions": 10,
            "deletions": 0
        }
        md = format_review_markdown(analysis, "https://github.com/foo/bar/pull/1")
        self.assertIn("## 🤖 Claude Code Review Summary", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score", md)
        self.assertIn("`Medium`", md)

if __name__ == "__main__":
    unittest.main()
