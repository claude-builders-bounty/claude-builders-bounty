import unittest

from pr_review_agent.cli import analyze_diff, diff_url, format_review, parse_pr_url


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 print("hello")
+subprocess.run(command)
"""


class PrReviewAgentTest(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_diff_url(self):
        self.assertEqual(
            diff_url("https://github.com/owner/repo/pull/123"),
            "https://github.com/owner/repo/pull/123.diff",
        )

    def test_analyze_diff_outputs_required_sections(self):
        review = analyze_diff(SAMPLE_DIFF)
        output = format_review("https://github.com/owner/repo/pull/123", review)
        self.assertIn("### Summary of changes", output)
        self.assertIn("### Identified risks", output)
        self.assertIn("### Improvement suggestions", output)
        self.assertIn("### Confidence score:", output)

    def test_detects_command_execution_risk(self):
        review = analyze_diff(SAMPLE_DIFF)
        self.assertTrue(any("command execution" in risk for risk in review.risks))


if __name__ == "__main__":
    unittest.main()
