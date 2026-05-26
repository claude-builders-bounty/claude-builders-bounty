import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory of agents/pr-reviewer to path so we can import claude_review
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import claude_review

class TestPRReviewer(unittest.TestCase):

    def test_parse_pr_url_valid(self):
        owner, repo, pr_number = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr_number, "123")

        owner, repo, pr_number = claude_review.parse_pr_url("github.com/another-owner/some-repo/pull/999")
        self.assertEqual(owner, "another-owner")
        self.assertEqual(repo, "some-repo")
        self.assertEqual(pr_number, "999")

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(SystemExit):
            with patch('claude_review.log') as mock_log:
                claude_review.parse_pr_url("https://github.com/owner/repo/issues/123")

    @patch('claude_review.make_http_request')
    def test_fetch_pr_details(self, mock_http):
        mock_http.side_effect = [
            ('{"title": "Test PR", "body": "Hello world"}', 200),
            ('some diff content', 200)
        ]
        metadata, diff = claude_review.fetch_pr_details("owner", "repo", "123", "dummy-token")
        self.assertEqual(metadata["title"], "Test PR")
        self.assertEqual(diff, "some diff content")
        self.assertEqual(mock_http.call_count, 2)

    @patch('claude_review.make_http_request')
    def test_post_pr_comment(self, mock_http):
        mock_http.return_value = ('{"id": 1}', 201)
        res = claude_review.post_pr_comment("owner", "repo", "123", "dummy-token", "Review body")
        self.assertTrue(res)
        mock_http.assert_called_once()

    @patch('claude_review.make_http_request')
    def test_call_claude_api(self, mock_http):
        mock_http.return_value = (json.dumps({
            "content": [{"text": "### Summary of Changes\nThis is a review."}]
        }), 200)
        review = claude_review.call_claude_api("dummy-api-key", "claude-model", "Title", "Body", "diff")
        self.assertIn("Summary of Changes", review)
        mock_http.assert_called_once()

if __name__ == "__main__":
    unittest.main()
