import unittest

from claude_review import confidence, detect_risks, parse_diff, render_markdown


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 print("hello")
+import subprocess
+subprocess.run(user_input, shell=True)
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_diff_counts_files_and_lines(self):
        stats = parse_diff(SAMPLE_DIFF)

        self.assertEqual(stats.files, ["app.py"])
        self.assertEqual(stats.additions, 2)
        self.assertEqual(stats.deletions, 0)
        self.assertEqual(stats.hunks, 1)

    def test_risk_and_markdown_output(self):
        stats = parse_diff(SAMPLE_DIFF)
        risks = detect_risks(stats)
        markdown = render_markdown(stats, "example/repo#1")

        self.assertTrue(any("shell-adjacent" in risk for risk in risks))
        self.assertIn("### Summary", markdown)
        self.assertIn("### Identified Risks", markdown)
        self.assertIn("### Improvement Suggestions", markdown)
        self.assertIn("### Confidence", markdown)
        self.assertEqual(confidence(stats, risks), "Medium")


if __name__ == "__main__":
    unittest.main()
