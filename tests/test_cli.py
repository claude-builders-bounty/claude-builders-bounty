import unittest

from claude_review.cli import analyze_diff, parse_pr_url, render_markdown


SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
 def login(user):
-    return True
+    token = user.session_token
+    return token is not None
diff --git a/tests/test_app.py b/tests/test_app.py
index 3333333..4444444 100644
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1,2 +1,5 @@
 def test_login():
-    assert True
+    assert login(user_with_session())
"""


class CliTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = parse_pr_url("https://github.com/owner/repo/pull/123")

        self.assertEqual(ref.owner, "owner")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 123)
        self.assertEqual(ref.diff_url, "https://github.com/owner/repo/pull/123.diff")

    def test_analyze_diff_detects_security_and_tests(self):
        review = analyze_diff(SAMPLE_DIFF)

        self.assertEqual(review.additions, 3)
        self.assertEqual(review.deletions, 2)
        self.assertEqual(review.confidence, "Low")
        self.assertTrue(any("Security-sensitive" in risk for risk in review.risks))

    def test_render_markdown_contains_required_sections(self):
        markdown = render_markdown(analyze_diff(SAMPLE_DIFF), "sample.diff")

        self.assertIn("## Summary of Changes", markdown)
        self.assertIn("## Identified Risks", markdown)
        self.assertIn("## Improvement Suggestions", markdown)
        self.assertIn("## Confidence Score:", markdown)


if __name__ == "__main__":
    unittest.main()
