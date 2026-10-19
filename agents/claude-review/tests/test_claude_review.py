import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_review.github_client import GitHubClient
from claude_review.analyzer import DiffAnalyzer

SAMPLE_DIFF = """diff --git a/server/app.py b/server/app.py
index 1234567..89abcdef 100644
--- a/server/app.py
+++ b/server/app.py
@@ -10,6 +10,8 @@ def handle_request(req):
-    return render_template("index.html")
+    user_input = req.args.get("q")
+    eval(user_input)
+    return {"status": "ok"}
"""

class TestClaudeReview(unittest.TestCase):
    def test_parse_pr_url(self):
        owner, repo, pr_num = GitHubClient.parse_pr_url("https://github.com/octocat/Spoon-Knife/pull/42")
        self.assertEqual(owner, "octocat")
        self.assertEqual(repo, "Spoon-Knife")
        self.assertEqual(pr_num, 42)

    def test_parse_pr_shorthand(self):
        owner, repo, pr_num = GitHubClient.parse_pr_url("octocat/Spoon-Knife#42")
        self.assertEqual(owner, "octocat")
        self.assertEqual(repo, "Spoon-Knife")
        self.assertEqual(pr_num, 42)

    def test_static_analyzer_structure(self):
        analyzer = DiffAnalyzer()
        pr_meta = {
            "title": "Add eval route",
            "author": "hacker",
            "number": 1,
            "base_branch": "main",
            "head_branch": "patch-1"
        }
        review = analyzer.analyze(pr_meta, SAMPLE_DIFF)
        self.assertIn("### 📋 Summary of Changes", review)
        self.assertIn("### ⚠️ Identified Risks", review)
        self.assertIn("### 💡 Improvement Suggestions", review)
        self.assertIn("### 🎯 Confidence Score:", review)
        self.assertIn("Security Risk", review)

if __name__ == "__main__":
    unittest.main()
