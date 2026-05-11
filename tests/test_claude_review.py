import importlib.util
import pathlib
import sys
import unittest
from importlib.machinery import SourceFileLoader


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "claude-review"
loader = SourceFileLoader("claude_review", str(MODULE_PATH))
spec = importlib.util.spec_from_loader("claude_review", loader)
claude_review = importlib.util.module_from_spec(spec)
sys.modules["claude_review"] = claude_review
spec.loader.exec_module(claude_review)


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self):
        pr = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")

        self.assertEqual(pr.owner, "owner")
        self.assertEqual(pr.repo, "repo")
        self.assertEqual(pr.number, 123)

    def test_detects_secret_and_missing_tests(self):
        diff = """diff --git a/app.py b/app.py
++ b/app.py
+API_KEY = "abc123"
+def handler():
+    return "ok"
"""

        stats = claude_review.diff_stats(diff)
        risks = claude_review.detect_risks(diff, stats)

        self.assertTrue(any("secret" in risk.lower() for risk in risks))
        self.assertTrue(any("tests" in risk.lower() for risk in risks))

    def test_delete_with_where_not_flagged_as_destructive_sql(self):
        diff = """diff --git a/query.sql b/query.sql
++ b/query.sql
+DELETE FROM sessions WHERE expires_at < now();
"""

        stats = claude_review.diff_stats(diff)
        risks = claude_review.detect_risks(diff, stats)

        self.assertFalse(any("destructive sql" in risk.lower() for risk in risks))

    def test_render_review_has_required_sections(self):
        pr = claude_review.PullRequest("owner", "repo", 1, "Add feature", "dev")
        diff = """diff --git a/tests/test_app.py b/tests/test_app.py
++ b/tests/test_app.py
+def test_app():
+    assert True
"""

        review = claude_review.render_review(pr, diff)

        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertIn("**Confidence:**", review)


if __name__ == "__main__":
    unittest.main()
