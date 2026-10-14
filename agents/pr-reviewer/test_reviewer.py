import unittest
from claude_review import parse_pr_url, analyze_diff, format_markdown_review

class TestPRReviewer(unittest.TestCase):
    def test_parse_pr_url(self):
        owner, repo, num = parse_pr_url("https://github.com/facebook/react/pull/12345")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(num, "12345")

    def test_clean_diff_approval(self):
        sample_diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
 def main():
+    print("Hello, world!")
     return 0
diff --git a/test_app.py b/test_app.py
--- a/test_app.py
+++ b/test_app.py
@@ -1,2 +1,3 @@
 def test_main():
+    assert main() == 0
"""
        analysis = analyze_diff(sample_diff)
        self.assertEqual(analysis["verdict"], "APPROVE")
        self.assertEqual(analysis["files_count"], 2)

    def test_dangerous_diff_detection(self):
        dangerous_diff = """diff --git a/cleanup.sh b/cleanup.sh
--- a/cleanup.sh
+++ b/cleanup.sh
@@ -1,2 +1,3 @@
 #!/bin/bash
+rm -rf /var/cache/data
+password = "secret_12345"
"""
        analysis = analyze_diff(dangerous_diff)
        self.assertEqual(analysis["verdict"], "REQUEST_CHANGES")
        self.assertTrue(any("rm -rf" in r for r in analysis["risks"]))
        self.assertTrue(any("secret" in r for r in analysis["risks"]))

    def test_markdown_formatting(self):
        analysis = {
            "summary": "Sample summary text.",
            "risks": ["Risk 1"],
            "suggestions": ["Suggestion 1"],
            "verdict": "APPROVE",
            "files_count": 1
        }
        md = format_markdown_review(analysis)
        self.assertIn("## 🤖 Revue Automatisée", md)
        self.assertIn("🟢 **APPROVE**", md)
        self.assertIn("- Risk 1", md)

if __name__ == "__main__":
    unittest.main()
