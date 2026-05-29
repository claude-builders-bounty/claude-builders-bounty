import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "claude-review.py"
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = claude_review.parse_pr_url("https://github.com/example/project/pull/123")
        self.assertEqual(ref.owner, "example")
        self.assertEqual(ref.repo, "project")
        self.assertEqual(ref.number, 123)

    def test_rejects_invalid_pr_url(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/example/project/issues/123")

    def test_changed_files_and_stats(self):
        diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1,2 @@
-old
+new
+extra
"""
        self.assertEqual(claude_review.changed_files(diff), ["a.py"])
        self.assertEqual(claude_review.diff_stats(diff), (2, 1))

    def test_heuristic_output_has_required_sections(self):
        metadata = {"title": "Add script", "html_url": "https://github.com/o/r/pull/1"}
        diff = """diff --git a/tool.py b/tool.py
--- a/tool.py
+++ b/tool.py
@@ -0,0 +1,2 @@
+print("hello")
+token = "placeholder"
"""
        output = claude_review.heuristic_review(metadata, diff)
        claude_review.validate_sections(output)
        self.assertIn("## Summary", output)
        self.assertIn("## Identified Risks", output)
        self.assertIn("## Improvement Suggestions", output)
        self.assertRegex(output, r"## Confidence\n(High|Medium|Low)")


if __name__ == "__main__":
    unittest.main()
