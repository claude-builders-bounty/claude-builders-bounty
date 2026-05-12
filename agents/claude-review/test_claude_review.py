import importlib.util
import importlib.machinery
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("claude-review")
SPEC = importlib.util.spec_from_loader(
    "claude_review",
    importlib.machinery.SourceFileLoader("claude_review", str(MODULE_PATH)),
)
review = importlib.util.module_from_spec(SPEC)
sys.modules["claude_review"] = review
SPEC.loader.exec_module(review)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            review.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_detects_secret_like_assignment_and_missing_tests(self):
        pr = review.PullRequest(
            owner="owner",
            repo="repo",
            number="1",
            title="Example",
            author="user",
            additions=10,
            deletions=2,
            changed_files=1,
            diff="+++ b/app.py\n+API_KEY = 'abc'\n",
        )
        risks = "\n".join(review.detect_risks(pr))
        self.assertIn("secret-like", risks)
        self.assertIn("No obvious test", risks)

    def test_markdown_contains_required_sections(self):
        pr = review.PullRequest(
            owner="owner",
            repo="repo",
            number="1",
            title="Example",
            author="user",
            additions=10,
            deletions=2,
            changed_files=2,
            diff="+++ b/src/app.ts\n+++ b/src/app.test.ts\n",
        )
        body = review.review_markdown(pr)
        self.assertIn("### Summary", body)
        self.assertIn("### Identified Risks", body)
        self.assertIn("### Improvement Suggestions", body)
        self.assertIn("### Confidence Score", body)


if __name__ == "__main__":
    unittest.main()
