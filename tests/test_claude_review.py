import importlib.util
import importlib.machinery
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("claude_review", str(ROOT / "claude-review"))
SPEC = importlib.util.spec_from_loader("claude_review", LOADER)
claude_review = importlib.util.module_from_spec(SPEC)
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        pr = claude_review.parse_pr_url("https://github.com/octocat/Hello-World/pull/42")
        self.assertEqual(pr.owner, "octocat")
        self.assertEqual(pr.repo, "Hello-World")
        self.assertEqual(pr.number, "42")

    def test_rejects_non_pr_url(self):
        with self.assertRaises(SystemExit):
            claude_review.parse_pr_url("https://github.com/octocat/Hello-World/issues/42")

    def test_build_review_contains_required_sections(self):
        context = claude_review.ReviewContext(
            pr=claude_review.PullRequest("owner", "repo", "7", "https://github.com/owner/repo/pull/7"),
            title="Add auth middleware",
            author="alice",
            changed_files=["src/auth.ts", "README.md"],
            additions=40,
            deletions=5,
            patch="+const token = request.headers.authorization\n+// TODO: add tests\n",
        )
        review = claude_review.build_review(context)
        self.assertIn("## Summary", review)
        self.assertIn("## Risks", review)
        self.assertIn("## Suggestions", review)
        self.assertIn("## Confidence:", review)
        self.assertIn("authentication or authorization-sensitive", review)

    def test_low_risk_review_gets_high_confidence(self):
        context = claude_review.ReviewContext(
            pr=claude_review.PullRequest("owner", "repo", "8", "https://github.com/owner/repo/pull/8"),
            title="Tighten copy",
            author="bob",
            changed_files=["src/copy.test.ts"],
            additions=8,
            deletions=3,
            patch="+expect(title).toContain('Hello')\n",
        )
        self.assertIn("## Confidence: High", claude_review.build_review(context))

    def test_format_comment_body_wraps_review(self):
        body = claude_review.format_comment_body("## Summary\nLooks good.")
        self.assertTrue(body.startswith("## Claude Review Agent"))
        self.assertIn("## Summary", body)
        self.assertTrue(body.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
