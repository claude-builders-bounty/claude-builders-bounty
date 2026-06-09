#!/usr/bin/env python3
import unittest

from claude_review import analyze_diff, render_review


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,8 @@
 import os
+import subprocess
+
+def delete_everything(path):
+    subprocess.run("rm -rf " + path, shell=True)
+
 def hello():
     return "hi"
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_analyze_diff_extracts_summary_risks_and_suggestions(self):
        result = analyze_diff(SAMPLE_DIFF)
        self.assertEqual(result.files_changed, 1)
        self.assertGreater(result.added_lines, 0)
        self.assertTrue(any("shell=True" in risk for risk in result.risks))
        self.assertTrue(any("subprocess" in suggestion for suggestion in result.suggestions))
        self.assertEqual(result.confidence, "High")

    def test_render_review_has_required_sections(self):
        rendered = render_review(analyze_diff(SAMPLE_DIFF), "https://github.com/o/r/pull/1")
        self.assertIn("## Summary", rendered)
        self.assertIn("## Identified Risks", rendered)
        self.assertIn("## Improvement Suggestions", rendered)
        self.assertIn("## Confidence", rendered)
        self.assertIn("High", rendered)


if __name__ == "__main__":
    unittest.main()
