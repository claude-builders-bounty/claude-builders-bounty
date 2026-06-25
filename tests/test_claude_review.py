#!/usr/bin/env python3
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from claude_review import get_pr_diff, call_claude_api

class TestClaudeReview(unittest.TestCase):
    
    def test_invalid_pr_url(self):
        invalid_urls = [
            "https://github.com/owner/repo",
            "https://google.com",
            "https://github.com/owner/repo/pull/abc",
            "invalid_string"
        ]
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                get_pr_diff(url)
                
    @patch('urllib.request.urlopen')
    def test_get_pr_diff_success(self, mock_urlopen):
        # Mock response inside context manager
        mock_response = MagicMock()
        mock_response.read.return_value = b"diff data"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        pr_url = "https://github.com/owner/repo/pull/123"
        diff = get_pr_diff(pr_url)
        self.assertEqual(diff, "diff data")
        mock_urlopen.assert_called_once()
        
    @patch('urllib.request.urlopen')
    def test_call_claude_api_success(self, mock_urlopen):
        # Mock response inside context manager
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"content": [{"text": "markdown review comment"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        diff = "some git diff"
        api_key = "test_key"
        review = call_claude_api(diff, api_key)
        self.assertEqual(review, "markdown review comment")
        mock_urlopen.assert_called_once()

if __name__ == '__main__':
    unittest.main()
