from __future__ import annotations

import unittest

from scripts.claude_review import PullRequest, detect_risks, parse_pr_url, render_review


class ClaudeReviewTests(unittest.TestCase):
    def sample_pr(self) -> PullRequest:
        return PullRequest(
            owner="owner",
            repo="repo",
            number=123,
            title="Add feature",
            body="",
            changed_files=2,
            additions=40,
            deletions=5,
            files=[
                {"filename": "src/app.py", "additions": 30, "deletions": 2, "status": "modified"},
                {"filename": "tests/test_app.py", "additions": 10, "deletions": 3, "status": "modified"},
            ],
        )

    def test_parse_pr_url(self) -> None:
        self.assertEqual(
            parse_pr_url("https://github.com/example/project/pull/456"),
            ("example", "project", 456),
        )

    def test_render_review_has_required_sections(self) -> None:
        review = render_review(self.sample_pr())
        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertRegex(review, r"### Confidence: (Low|Medium|High)")

    def test_detects_security_risk(self) -> None:
        pr = PullRequest(
            owner="owner",
            repo="repo",
            number=1,
            title="Auth change",
            body="",
            changed_files=1,
            additions=20,
            deletions=0,
            files=[{"filename": "lib/auth/session.ts", "status": "modified"}],
        )
        self.assertTrue(any("Authentication" in risk for risk in detect_risks(pr)))


if __name__ == "__main__":
    unittest.main()
