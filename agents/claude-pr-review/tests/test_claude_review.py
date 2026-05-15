import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "claude_review.py"
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = claude_review
SPEC.loader.exec_module(claude_review)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url_accepts_canonical_pull_request_url(self):
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_parse_pr_url_rejects_non_pull_request_url(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/owner/repo/issues/123")

    def test_diff_stats_collects_files_and_changed_lines(self):
        diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,2 +1,2 @@
-old setup
+new setup
diff --git a/tests/test_cli.py b/tests/test_cli.py
--- /dev/null
+++ b/tests/test_cli.py
@@ -0,0 +1 @@
+def test_cli(): pass
"""

        stats = claude_review.diff_stats(diff)

        self.assertEqual(stats.files, {"README.md", "tests/test_cli.py"})
        self.assertEqual(stats.additions, 2)
        self.assertEqual(stats.deletions, 1)

    def test_render_review_includes_required_sections(self):
        stats = claude_review.diff_stats(
            """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -0,0 +1,2 @@
+API_KEY = "example"
+print(API_KEY)
"""
        )

        review = claude_review.render_review(
            "https://github.com/owner/repo/pull/123",
            stats,
        )

        self.assertIn("### Summary of Changes", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertIn("### Confidence Score:", review)
        self.assertIn("sensitive credential terms", review)


if __name__ == "__main__":
    unittest.main()
