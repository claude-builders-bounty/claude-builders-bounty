import unittest

from claude_review.cli import parse_diff, parse_pr_url, render_review


class ClaudeReviewCliTest(unittest.TestCase):
    def test_parse_pr_url_accepts_github_pull_request_url(self):
        self.assertEqual(
            parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_parse_diff_counts_files_and_lines(self):
        raw_diff = """diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Title
-old line
+new line
+second line
diff --git a/src/app.py b/src/app.py
index 3333333..4444444 100644
--- a/src/app.py
+++ b/src/app.py
@@ -10,2 +10,2 @@
-print("old")
+print("new")
"""
        summary = parse_diff(raw_diff, "https://github.com/owner/repo/pull/123")

        self.assertEqual(len(summary.files), 2)
        self.assertEqual(summary.total_added, 3)
        self.assertEqual(summary.total_removed, 2)
        self.assertEqual(summary.files[0].path, "README.md")
        self.assertEqual(summary.files[1].path, "src/app.py")

    def test_render_review_includes_required_sections(self):
        raw_diff = """diff --git a/src/app.py b/src/app.py
index 3333333..4444444 100644
--- a/src/app.py
+++ b/src/app.py
@@ -10,2 +10,2 @@
-print("old")
+print("new")
"""
        summary = parse_diff(raw_diff, "https://github.com/owner/repo/pull/123")
        review = render_review(summary)

        self.assertIn("## Summary of changes", review)
        self.assertIn("## Identified risks", review)
        self.assertIn("## Improvement suggestions", review)
        self.assertIn("## Confidence score:", review)


if __name__ == "__main__":
    unittest.main()
