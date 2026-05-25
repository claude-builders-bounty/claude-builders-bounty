from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_review import markdown_review, parse_diff, pr_diff_url


SAMPLE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index 1111111..2222222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,2 +1,5 @@
+API_TOKEN = "example"
+def check_role(user):
+    return user.role == "admin"
 def ok():
     return True
diff --git a/tests/test_auth.py b/tests/test_auth.py
index 3333333..4444444 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -0,0 +1,2 @@
+def test_check_role():
+    assert True
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_pr_diff_url(self) -> None:
        self.assertEqual(
            pr_diff_url("https://github.com/example/project/pull/123"),
            "https://github.com/example/project/pull/123.diff",
        )

    def test_pr_diff_url_rejects_non_pr_url(self) -> None:
        with self.assertRaises(ValueError):
            pr_diff_url("https://github.com/example/project/issues/123")

    def test_parse_diff_counts_changes_and_flags(self) -> None:
        facts = parse_diff(SAMPLE_DIFF)
        self.assertEqual(len(facts.files), 2)
        self.assertEqual(facts.additions, 5)
        self.assertEqual(facts.deletions, 0)
        self.assertTrue(facts.has_tests)
        self.assertTrue(facts.touches_security_sensitive)

    def test_markdown_has_required_sections(self) -> None:
        review = markdown_review(SAMPLE_DIFF)
        self.assertIn("## Summary of Changes", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertIn("## Confidence Score", review)
        self.assertIn("Security-sensitive", review)


if __name__ == "__main__":
    unittest.main()
