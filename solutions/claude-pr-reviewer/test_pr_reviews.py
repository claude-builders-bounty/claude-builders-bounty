import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import urllib.error

import importlib.machinery
import importlib.util

# Load claude-review module dynamically since it has no .py extension
loader = importlib.machinery.SourceFileLoader(
    "claude_review",
    os.path.join(os.path.dirname(__file__), "claude-review")
)
spec = importlib.util.spec_from_loader("claude_review", loader)
claude_review = importlib.util.module_from_spec(spec)
loader.exec_module(claude_review)

class TestPRReviewer(unittest.TestCase):

    def test_parse_pr_url_valid(self):
        url = "https://github.com/typeorm/typeorm/pull/12578"
        res = claude_review.parse_pr_url(url)
        self.assertEqual(res["owner"], "typeorm")
        self.assertEqual(res["repo"], "typeorm")
        self.assertEqual(res["number"], "12578")

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/invalid/url")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"pull_request": {"html_url": "https://github.com/owner/repo/pull/123"}}')
    def test_get_pr_url_from_event_pull_request(self, mock_file, mock_exists):
        mock_exists.return_value = True
        with patch.dict(os.environ, {"GITHUB_EVENT_PATH": "/tmp/event.json"}):
            url = claude_review.get_pr_url_from_event()
            self.assertEqual(url, "https://github.com/owner/repo/pull/123")

    @patch("urllib.request.urlopen")
    def test_fetch_diff_success(self, mock_urlopen):
        # Mock response
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"diff --git a/file.py b/file.py\n+new line"
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        diff = claude_review.fetch_diff("owner", "repo", "123")
        self.assertIn("+new line", diff)

    @patch("urllib.request.urlopen")
    def test_fetch_diff_error(self, mock_urlopen):
        # Mock HTTP error
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"Not Found"
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.github.com", 404, "Not Found", {}, mock_resp
        )

        with self.assertRaises(RuntimeError):
            claude_review.fetch_diff("owner", "repo", "123")

    @patch("urllib.request.urlopen")
    def test_call_claude_success(self, mock_urlopen):
        # Mock Claude response payload
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [
                {
                    "text": "### Summary of Changes\nFixed a bug.\n\n**Confidence score**: High"
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        review = claude_review.call_claude("diff --git a/file1.py b/file1.py\n+new line", "fake_key")
        self.assertIn("Summary of Changes", review)
        self.assertIn("Confidence score", review)
        self.assertIn("(reviewed 1 of 1 files)", review)

    @patch("urllib.request.urlopen")
    def test_call_claude_multiple_files_and_truncation(self, mock_urlopen):
        # Mock Claude response payload
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [
                {
                    "text": "### Summary of Changes\nFixed bugs.\n\n**Confidence score**: High"
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        # Create a huge diff containing 3 files
        large_diff = (
            "diff --git a/file1.py b/file1.py\n" + "x" * 50000 + "\n"
            "diff --git a/file2.py b/file2.py\n" + "y" * 60000 + "\n"
            "diff --git a/file3.py b/file3.py\n" + "z" * 1000 + "\n"
        )
        
        review = claude_review.call_claude(large_diff, "fake_key")
        self.assertIn("Confidence score", review)
        self.assertIn("(reviewed 2 of 3 files)", review)

if __name__ == "__main__":
    unittest.main()
