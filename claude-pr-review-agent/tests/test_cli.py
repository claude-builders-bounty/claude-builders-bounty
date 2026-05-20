import unittest

from claude_pr_review_agent.cli import (
    PullRequestRef,
    build_prompt,
    heuristic_review,
    parse_pr_url,
    truncate_diff,
)


class CliTest(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = parse_pr_url("https://github.com/example/project/pull/123")
        self.assertEqual(ref.owner, "example")
        self.assertEqual(ref.repo, "project")
        self.assertEqual(ref.number, 123)
        self.assertEqual(ref.repo_name, "example/project")

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/example/project/issues/123")

    def test_truncate_diff_keeps_short_diff(self):
        self.assertEqual(truncate_diff("abc", limit=10), "abc")

    def test_truncate_diff_marks_omission(self):
        result = truncate_diff("abcdef", limit=3)
        self.assertIn("abc", result)
        self.assertIn("diff truncated", result)

    def test_prompt_contains_required_sections_instruction(self):
        context = fake_context()
        prompt = build_prompt(context)
        self.assertIn("## Summary", prompt)
        self.assertIn("## Identified Risks", prompt)
        self.assertIn("## Improvement Suggestions", prompt)
        self.assertIn("## Confidence", prompt)
        self.assertIn("https://github.com/example/project/pull/7", prompt)

    def test_heuristic_review_has_required_sections(self):
        review = heuristic_review(fake_context())
        self.assertIn("## Summary", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertRegex(review, r"## Confidence\n(Low|Medium|High) - ")


def fake_context():
    return {
        "ref": PullRequestRef(owner="example", repo="project", number=7),
        "metadata": {
            "title": "Add review workflow",
            "author": {"login": "octocat"},
            "baseRefName": "main",
            "headRefName": "review-workflow",
            "changedFiles": 2,
            "additions": 40,
            "deletions": 2,
            "files": [
                {"path": ".github/workflows/review.yml", "additions": 30, "deletions": 0},
                {"path": "README.md", "additions": 10, "deletions": 2},
            ],
        },
        "diff": "diff --git a/README.md b/README.md\n+hello\n",
    }


if __name__ == "__main__":
    unittest.main()
