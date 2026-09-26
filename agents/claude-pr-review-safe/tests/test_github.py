import unittest
from unittest.mock import patch

from claude_review.github import (
    GitHubError,
    PullRequest,
    fetch_pull_request_diff,
    parse_pull_request_url,
)


class Response:
    def __init__(self, data: bytes, headers: dict[str, str] | None = None):
        self.data = data
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.data if size < 0 else self.data[:size]


class PullRequestUrlTests(unittest.TestCase):
    def test_accepts_canonical_public_pull_request_url(self):
        self.assertEqual(
            parse_pull_request_url("https://github.com/example/repo/pull/123"),
            PullRequest("example", "repo", 123),
        )
        self.assertEqual(
            parse_pull_request_url("https://github.com/example/repo.name/pull/123/"),
            PullRequest("example", "repo.name", 123),
        )

    def test_rejects_non_github_and_ambiguous_urls(self):
        invalid = (
            "http://github.com/example/repo/pull/123",
            "https://github.com.evil.example/example/repo/pull/123",
            "https://github.com/example/repo/pull/123?token=secret",
            "https://example:443@github.com/example/repo/pull/123",
            "https://github.com:443/example/repo/pull/123",
            "https://github.com/example/repo/issues/123",
            "https://github.com/example/repo/pull/0",
            "https://github.com/example/repo/pull/123/files",
        )
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(GitHubError):
                parse_pull_request_url(url)


class PullRequestDiffTests(unittest.TestCase):
    def test_fetches_only_a_bounded_diff(self):
        with patch(
            "claude_review.github.urllib.request.urlopen",
            return_value=Response(b"diff --git a/x b/x\n"),
        ) as open_url:
            diff = fetch_pull_request_diff(PullRequest("example", "repo", 1))
        self.assertIn("diff --git", diff)
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("application/vnd.github.diff", request.get_header("Accept"))

    def test_rejects_content_length_over_the_limit_without_reading(self):
        response = Response(b"too much", {"Content-Length": "100"})
        with patch(
            "claude_review.github.urllib.request.urlopen", return_value=response
        ):
            with self.assertRaisesRegex(GitHubError, "exceeds"):
                fetch_pull_request_diff(PullRequest("example", "repo", 1), max_bytes=10)

    def test_rejects_streamed_response_over_the_limit(self):
        with patch(
            "claude_review.github.urllib.request.urlopen",
            return_value=Response(b"123456"),
        ):
            with self.assertRaisesRegex(GitHubError, "exceeds"):
                fetch_pull_request_diff(PullRequest("example", "repo", 1), max_bytes=5)


if __name__ == "__main__":
    unittest.main()
