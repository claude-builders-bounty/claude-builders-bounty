import unittest

from claude_review.cli import PullRequest, deterministic_review, parse_pr_url


class ReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", 123),
        )

    def test_structured_markdown(self):
        pr = PullRequest(
            owner="owner",
            repo="repo",
            number=12,
            title="Fix authentication edge case",
            url="https://github.com/owner/repo/pull/12",
            diff=(
                "diff --git a/auth.py b/auth.py\n"
                "--- a/auth.py\n+++ b/auth.py\n"
                "@@ -1 +1,2 @@\n"
                "-return token\n+if token:\n+    return token\n"
            ),
        )
        out = deterministic_review(pr)
        self.assertIn("### Summary", out)
        self.assertIn("### Identified Risks", out)
        self.assertIn("### Improvement Suggestions", out)
        self.assertRegex(out, r"### Confidence: (Low|Medium|High)")

    def test_docs_only_review(self):
        pr = PullRequest(
            owner="owner",
            repo="repo",
            number=13,
            title="Clarify docs",
            url="https://github.com/owner/repo/pull/13",
            diff=(
                "diff --git a/docs/guide.md b/docs/guide.md\n"
                "--- a/docs/guide.md\n+++ b/docs/guide.md\n"
                "@@ -1 +1 @@\n-old\n+new\n"
            ),
        )
        out = deterministic_review(pr)
        self.assertIn("Documentation examples", out)


if __name__ == "__main__":
    unittest.main()
