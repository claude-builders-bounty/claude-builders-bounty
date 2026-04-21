#!/usr/bin/env python3
import unittest

from claude_review import analyze_diff, build_review, PullRequest


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 import os
+TOKEN = "example"
 print("ok")
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_analyze_diff_counts_files_and_lines(self) -> None:
        stats = analyze_diff(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["app.py"])
        self.assertEqual(stats.additions, 1)
        self.assertEqual(stats.deletions, 0)
        self.assertEqual(stats.code_files, ["app.py"])

    def test_build_review_has_required_sections(self) -> None:
        pr = PullRequest("owner", "repo", "1", "Demo PR", "alice", "https://github.com/owner/repo/pull/1", 1, 0, 1, SAMPLE_DIFF)
        review = build_review(pr)
        self.assertIn("### Summary of Changes", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertIn("### Confidence Score", review)


if __name__ == "__main__":
    unittest.main()
