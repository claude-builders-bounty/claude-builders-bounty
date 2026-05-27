import unittest

from agents.pr_reviewer_import import claude_review


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
+print("debug")
 def handler():
     return "ok"
diff --git a/tests/test_app.py b/tests/test_app.py
index 3333333..4444444 100644
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1 +1,2 @@
+def test_handler(): pass
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_render_contains_required_sections(self):
        stats = claude_review.parse_diff(SAMPLE_DIFF)
        review = claude_review.render_review("https://github.com/owner/repo/pull/123", stats)
        self.assertIn("### Summary of Changes", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertRegex(review, r"### Confidence Score: (Low|Medium|High)")


if __name__ == "__main__":
    unittest.main()
