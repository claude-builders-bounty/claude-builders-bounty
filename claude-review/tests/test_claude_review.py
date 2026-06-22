#!/usr/bin/env python3
"""Tests for claude-review."""

import unittest
from unittest.mock import patch, MagicMock
from claude_review import parse_pr_url, fetch_pr_diff, call_claude


class TestParsePRUrl(unittest.TestCase):
    def test_valid_url(self):
        owner, repo, pr = parse_pr_url("https://github.com/anthropics/claude-code/pull/42")
        self.assertEqual(owner, "anthropics")
        self.assertEqual(repo, "claude-code")
        self.assertEqual(pr, 42)

    def test_valid_url_with_http(self):
        owner, repo, pr = parse_pr_url("http://github.com/owner/repo/pull/1")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr, 1)

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://google.com/not-a-pr")

    def test_empty_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("")


class TestFetchPRDiff(unittest.TestCase):
    @patch("claude_review.subprocess.run")
    def test_successful_fetch(self, mock_run):
        mock_run.return_value = MagicMock(stdout="diff --git a/foo.py\n+hello", stderr="", returncode=0)
        diff = fetch_pr_diff("owner", "repo", 1)
        self.assertEqual(diff, "diff --git a/foo.py\n+hello")
        mock_run.assert_called_once_with(
            ["gh", "pr", "diff", "1", "--repo", "owner/repo"],
            capture_output=True, text=True, check=True,
        )

    @patch("claude_review.subprocess.run")
    def test_failed_fetch(self, mock_run):
        mock_run.side_effect = __import__("subprocess").CalledProcessError(1, "gh", stderr="not found")
        with self.assertRaises(SystemExit):
            fetch_pr_diff("owner", "repo", 1)


class TestCallClaude(unittest.TestCase):
    @patch("claude_review.urlopen")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_successful_call(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"content":[{"text":"Review looks good"}]}'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = call_claude("some diff")
        self.assertEqual(result, "Review looks good")

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key(self):
        with self.assertRaises(SystemExit):
            call_claude("some diff")


if __name__ == "__main__":
    unittest.main()
