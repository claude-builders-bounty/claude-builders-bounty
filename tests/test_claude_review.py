from importlib.machinery import SourceFileLoader
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "claude-review"
claude_review = SourceFileLoader("claude_review", str(MODULE_PATH)).load_module()


class ClaudeReviewTests(unittest.TestCase):
    def test_heuristic_review_uses_required_sections(self):
        diff = """diff --git a/app.py b/app.py
index 0000000..1111111 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
+print("hello")
"""

        output = claude_review.heuristic_review("https://github.com/example/repo/pull/1", diff)

        self.assertIn("## Summary", output)
        self.assertIn("## Identified Risks", output)
        self.assertIn("## Improvement Suggestions", output)
        self.assertIn("## Confidence", output)


    def test_heuristic_review_flags_missing_tests(self):
        diff = """diff --git a/app.py b/app.py
index 0000000..1111111 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
+subprocess.run(["echo", "hello"])
"""

        output = claude_review.heuristic_review("https://github.com/example/repo/pull/2", diff)

        self.assertIn("No obvious test files were changed", output)
        self.assertIn("subprocess", output)
        self.assertIn("Low", output)


if __name__ == "__main__":
    unittest.main()
