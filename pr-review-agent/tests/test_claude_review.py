#!/usr/bin/env python3
"""
Test suite for claude-review PR agent.
Tests parsing, diff fetching, and review generation without API calls.
"""

import unittest, tempfile, json, os, sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Import functions from the main script (extract them for testability)
from claude_review_lib import parse_pr_url, build_review_prompt, truncate_diff


class TestParsing(unittest.TestCase):
    def test_parse_pr_url(self):
        cases = [
            ("https://github.com/owner/repo/pull/123", ("owner/repo", 123)),
            ("https://github.com/my-org/my-repo/pull/4567", ("my-org/my-repo", 4567)),
        ]
        for url, expected in cases:
            self.assertEqual(parse_pr_url(url), expected)
    
    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://example.com/not-a-pr")


class TestPromptBuilding(unittest.TestCase):
    def test_build_review_prompt_structure(self):
        prompt = build_review_prompt("+some code", "owner/repo", 42)
        self.assertIn("## PR Diff", prompt)
        self.assertIn("owner/repo#42", prompt)
        self.assertIn("Summary of Changes", prompt)
        self.assertIn("Identified Risks", prompt)
        self.assertIn("Improvement Suggestions", prompt)
        self.assertIn("Confidence Score", prompt)
    
    def test_truncate_diff(self):
        long_diff = "+" * 20000
        result = truncate_diff(long_diff, max_chars=15000)
        self.assertLess(len(result), 16000)
        self.assertIn("[... diff truncated", result)


class TestDiffFetching(unittest.TestCase):
    @patch("claude_review_lib.requests.get")
    def test_fetch_pr_diff_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text="@@ -1,2 +1,3 @@\n+new line")
        from claude_review_lib import fetch_pr_diff
        result = fetch_pr_diff("owner/repo", 1, "fake-token")
        self.assertIn("new line", result)
        mock_get.assert_called_once()


class TestReviewPosting(unittest.TestCase):
    @patch("claude_review_lib.requests.post")
    def test_post_github_comment(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"html_url": "https://github.com/owner/repo/issues/1#issuecomment-123"}
        )
        from claude_review_lib import post_github_comment
        url = post_github_comment("owner/repo", 1, "# Review", "fake-token")
        self.assertIn("github.com", url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
