import unittest
from unittest.mock import patch

from pr_review_agent_import import claude_review


SAMPLE_DIFF = """diff --git a/app/auth/session.py b/app/auth/session.py
index 1111111..2222222 100644
--- a/app/auth/session.py
+++ b/app/auth/session.py
@@ -1,2 +1,4 @@
+TOKEN = "hardcoded-secret-value"
+def validate_session(user):
+    return bool(user)
diff --git a/tests/test_session.py b/tests/test_session.py
index 3333333..4444444 100644
--- a/tests/test_session.py
+++ b/tests/test_session.py
@@ -0,0 +1,2 @@
+def test_validate_session():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = claude_review.parse_pr_url("https://github.com/example/project/pull/42")
        self.assertEqual(ref.repo_name, "example/project")
        self.assertEqual(ref.number, 42)

    def test_parse_pr_url_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://example.com/not-a-pr")

    def test_parse_diff_counts_files_and_lines(self):
        files = claude_review.parse_diff(SAMPLE_DIFF)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].path, "app/auth/session.py")
        self.assertEqual(files[0].additions, 3)

    def test_risks_include_auth_and_secret(self):
        files = claude_review.parse_diff(SAMPLE_DIFF)
        risks = claude_review.classify_risks(files, total_delta=5)
        joined = "\n".join(risks)
        self.assertIn("auth/session/security surface changed", joined)
        self.assertIn("possible secret or credential literal", joined)

    def test_confidence_high_for_small_tested_doc_change(self):
        files = [claude_review.FileChange("tests/test_readme.py", additions=2)]
        risks = ["- No obvious high-risk patterns were detected by the local rules."]
        self.assertEqual(claude_review.confidence_score(files, risks, total_delta=2), "High")

    @patch.object(claude_review, "fetch_pr_metadata")
    @patch.object(claude_review, "fetch_pr_diff")
    def test_render_markdown_has_required_sections(self, mock_diff, mock_meta):
        mock_diff.return_value = SAMPLE_DIFF
        mock_meta.return_value = {
            "title": "Example PR",
            "url": "https://github.com/example/project/pull/42",
            "additions": 5,
            "deletions": 0,
            "files": [],
        }
        rendered = claude_review.render_markdown(
            claude_review.analyze("https://github.com/example/project/pull/42")
        )
        self.assertIn("## Summary of Changes", rendered)
        self.assertIn("## Identified Risks", rendered)
        self.assertIn("## Improvement Suggestions", rendered)
        self.assertIn("## Confidence Score", rendered)


if __name__ == "__main__":
    unittest.main()
