import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add current directory to path so we can import the script
sys.path.append(os.getcwd())

class TestClaudeReview(unittest.TestCase):
    @patch('urllib.request.urlopen')
    def test_get_pr_diff(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"diff --git a/file.txt b/file.txt\n+hello"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        from claude_review import get_pr_diff
        diff = get_pr_diff("https://github.com/test/repo/pull/1")
        self.assertEqual(diff, "diff --git a/file.txt b/file.txt\n+hello")

    @patch('urllib.request.urlopen')
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_analyze_diff(self, mock_urlopen):
        mock_response = MagicMock()
        # Ensure we use raw bytes with simple ASCII to avoid decoding issues during the test
        response_json = json.dumps({"content": [{"text": "### Summary of Changes\nTest summary"}]})
        mock_response.read.return_value = response_json.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        from claude_review import analyze_diff
        review = analyze_diff("some diff", "test_key")
        self.assertIsNotNone(review, "Review should not be None")
        self.assertIn("### Summary of Changes", review)

if __name__ == "__main__":
    unittest.main()
