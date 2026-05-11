import unittest

from pathlib import Path
import importlib.machinery


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "claude-review"
loader = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT))
claude_review = loader.load_module()


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = claude_review.parse_pr_url("https://github.com/example/repo/pull/123")
        self.assertEqual(ref.full_name, "example/repo")
        self.assertEqual(ref.number, 123)

    def test_render_review_has_required_sections(self):
        pr = {
            "title": "fix: protect workspace access",
            "additions": 20,
            "deletions": 4,
            "files": [
                {"path": "app/workspaces/page.tsx"},
                {"path": "tests/workspace_access.test.ts"},
            ],
        }
        body = claude_review.render_review(pr, "diff --git a/app/workspaces/page.tsx b/app/workspaces/page.tsx")

        self.assertIn("### Summary Of Changes", body)
        self.assertIn("### Identified Risks", body)
        self.assertIn("### Improvement Suggestions", body)
        self.assertIn("### Confidence Score", body)
        self.assertIn("High", body)

    def test_flags_missing_tests_and_destructive_sql(self):
        pr = {
            "title": "cleanup sessions",
            "additions": 10,
            "deletions": 2,
            "files": [{"path": "db/queries/sessions.ts"}],
        }
        risks = claude_review.classify_risks(pr, "DELETE FROM sessions")

        self.assertTrue(any("No obvious tests" in risk for risk in risks))
        self.assertTrue(any("Destructive SQL" in risk for risk in risks))


if __name__ == "__main__":
    unittest.main()
