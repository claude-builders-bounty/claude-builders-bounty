from __future__ import annotations

import unittest

from tools.claude_review.claude_review import analyze_diff, parse_pr_url, review_diff


SIMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 print("hello")
+eval(user_input)
+print("done")
"""


TEST_DIFF = """diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,3 @@
+def test_app():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        self.assertEqual(
            parse_pr_url("https://github.com/example/project/pull/123"),
            ("example/project", 123),
        )

    def test_detects_risky_diff_and_missing_tests(self) -> None:
        analysis = analyze_diff(SIMPLE_DIFF)
        self.assertEqual(len(analysis.files), 1)
        self.assertEqual(analysis.additions, 2)
        self.assertTrue(any("eval-like" in risk for risk in analysis.risks))
        self.assertTrue(any("No test files" in risk for risk in analysis.risks))
        self.assertEqual(analysis.confidence, "Medium")

    def test_test_only_diff_can_be_high_confidence(self) -> None:
        analysis = analyze_diff(TEST_DIFF)
        self.assertEqual(analysis.confidence, "High")
        self.assertFalse(any("No test files" in risk for risk in analysis.risks))

    def test_review_output_has_required_sections(self) -> None:
        markdown = review_diff(SIMPLE_DIFF, "https://github.com/example/project/pull/123")
        self.assertIn("### Summary", markdown)
        self.assertIn("### Identified risks", markdown)
        self.assertIn("### Improvement suggestions", markdown)
        self.assertIn("### Confidence score", markdown)


if __name__ == "__main__":
    unittest.main()
