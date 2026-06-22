import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "claude_review.py"
spec = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["claude_review"] = claude_review
spec.loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 0000000..1111111 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 print("hello")
+token = "example"
+subprocess.run(["echo", "x"])
diff --git a/tests/test_app.py b/tests/test_app.py
index 0000000..2222222 100644
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_app():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_diff_counts_files_and_lines(self):
        files = claude_review.parse_diff(SAMPLE_DIFF)

        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].path, "app.py")
        self.assertEqual(files[0].additions, 2)
        self.assertEqual(files[1].path, "tests/test_app.py")

    def test_render_review_contains_required_sections(self):
        files = claude_review.parse_diff(SAMPLE_DIFF)
        review = claude_review.render_review("https://github.com/example/repo/pull/1", files)

        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertRegex(review, r"### Confidence: (Low|Medium|High)")

    def test_github_diff_url_validation(self):
        self.assertEqual(
            claude_review.github_diff_url("https://github.com/owner/repo/pull/123"),
            "https://github.com/owner/repo/pull/123.diff",
        )
        with self.assertRaises(ValueError):
            claude_review.github_diff_url("https://example.com/not-a-pr")


if __name__ == "__main__":
    unittest.main()
