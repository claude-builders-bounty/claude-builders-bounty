import unittest

from claude_review import PullRequest, confidence, parse_pr_url, render, risks


class ReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(parse_pr_url("https://github.com/owner/repo/pull/42/files"), ("owner", "repo", 42))

    def test_parse_pr_url_rejects_non_pr(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/owner/repo/issues/42")

    def test_large_security_diff_is_low_confidence(self):
        pr = PullRequest(
            owner="owner", repo="repo", number=42, title="change auth", body="details",
            state="open", draft=False, additions=1200, deletions=500, changed_files=2,
            mergeable=False, files=({"filename": "src/auth.py"}, {"filename": "deploy.yml"}),
        )
        self.assertEqual(confidence(pr), "Low")
        self.assertTrue(any("Security-sensitive" in item for item in risks(pr)))
        output = render(pr)
        for heading in ("## Summary", "## Identified risks", "## Improvement suggestions", "## Confidence"):
            self.assertIn(heading, output)


if __name__ == "__main__":
    unittest.main()
