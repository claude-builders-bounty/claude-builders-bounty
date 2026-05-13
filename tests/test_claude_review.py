import unittest
from unittest.mock import patch

from tools.claude_review import (
    build_fallback_review,
    normalize_review,
    parse_pr_url,
    parse_review_json,
    post_pr_comment,
    render_markdown,
)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        owner, repo, number = parse_pr_url("https://github.com/openai/openai-python/pull/123")
        self.assertEqual((owner, repo, number), ("openai", "openai-python", 123))

    def test_parse_review_json_from_fenced_text(self) -> None:
        payload = '```json\n{"summary":"ok","risks":[],"suggestions":[],"confidence":"high"}\n```'
        review = parse_review_json(payload)
        normalized = normalize_review(review)
        self.assertEqual(normalized["confidence"], "High")

    def test_render_markdown_contains_required_sections(self) -> None:
        pr = {
            "number": 7,
            "base": {"repo": {"full_name": "example/repo"}},
        }
        review = {
            "summary": "Two sentence summary.",
            "risks": ["Risk 1"],
            "suggestions": ["Suggestion 1"],
            "confidence": "Medium",
        }
        markdown = render_markdown("https://github.com/example/repo/pull/7", pr, review)
        self.assertIn("## Summary", markdown)
        self.assertIn("## Identified Risks", markdown)
        self.assertIn("## Improvement Suggestions", markdown)
        self.assertIn("## Confidence", markdown)

    def test_build_fallback_review_returns_valid_shape(self) -> None:
        pr = {
            "changed_files": 2,
            "additions": 10,
            "deletions": 1,
        }
        files = [
            {"filename": "src/auth.ts", "patch": "+// TODO tighten session handling\n"},
            {"filename": "README.md", "patch": "+docs\n"},
        ]
        review = build_fallback_review(pr, files)
        normalized = normalize_review(review)
        self.assertIn("deterministic fallback analysis", normalized["summary"])
        self.assertTrue(normalized["risks"])
        self.assertTrue(normalized["suggestions"])

    @patch("tools.claude_review.run_curl")
    def test_post_pr_comment_uses_issue_comment_endpoint(self, run_curl) -> None:
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=False):
            post_pr_comment("example", "repo", 9, "hello review")

        run_curl.assert_called_once()
        url = run_curl.call_args.args[0]
        kwargs = run_curl.call_args.kwargs
        self.assertEqual(
            url,
            "https://api.github.com/repos/example/repo/issues/9/comments",
        )
        self.assertEqual(kwargs["method"], "POST")
        self.assertIn('"body": "hello review"', kwargs["data"])


if __name__ == "__main__":
    unittest.main()
