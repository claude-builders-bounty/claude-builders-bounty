import unittest

from claude_review_agent import parse_diff, parse_pr_url, render_local_review


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
 def login(user):
-    return True
+    if not user:
+        return False
+    return user.is_active
diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Demo
+Usage notes
"""


class PullRequestParsingTest(unittest.TestCase):
    def test_parse_pr_url(self):
        pr = parse_pr_url("https://github.com/example/project/pull/42")
        self.assertEqual(pr.owner, "example")
        self.assertEqual(pr.repo, "project")
        self.assertEqual(pr.number, "42")

    def test_parse_pr_url_rejects_non_pr(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/example/project/issues/42")


class DiffReviewTest(unittest.TestCase):
    def test_parse_diff_counts_files_and_changes(self):
        stats = parse_diff(SAMPLE_DIFF)
        self.assertEqual(len(stats.files), 2)
        self.assertEqual(stats.additions, 4)
        self.assertEqual(stats.deletions, 1)
        self.assertEqual(stats.files[0].path, "app.py")

    def test_render_review_has_required_sections(self):
        review = render_local_review("sample", SAMPLE_DIFF, max_chars=None)
        self.assertIn("### Summary of Changes", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertRegex(review, r"### Confidence Score: (Low|Medium|High)")
        self.assertIn("Code files changed", review)


if __name__ == "__main__":
    unittest.main()
