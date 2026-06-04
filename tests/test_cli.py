import unittest

from claude_review.cli import PullRequestRef, parse_pr_url, render_review


class ClaudeReviewCliTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = parse_pr_url("https://github.com/example/project/pull/123")
        self.assertEqual(ref, PullRequestRef(owner="example", repo="project", number="123"))

    def test_invalid_pr_url_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://example.com/not/a/github/pr")

    def test_render_review_contains_required_sections(self):
        diff = """diff --git a/app.py b/app.py
index 0000000..1111111 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
-print('old')
+print('new')
+def ok(): return True
"""
        review = render_review(PullRequestRef("example", "project", "1"), diff)
        self.assertIn("## PR Review Summary", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertIn("## Confidence Score", review)


if __name__ == "__main__":
    unittest.main()
