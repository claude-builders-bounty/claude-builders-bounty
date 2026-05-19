#!/usr/bin/env python3
"""
Simple test for the Claude Review Agent
"""

import unittest
from claude_review import ClaudeReviewer, GitHubClient, parse_pr_url


class TestClaudeReviewer(unittest.TestCase):

    def test_parse_pr_url(self):
        """Test parsing of PR URLs"""
        owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr_num, 123)

        # Test with trailing slash
        owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo/pull/123/")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr_num, 123)

    def test_claude_reviewer_init(self):
        """Test that ClaudeReviewer initializes correctly"""
        reviewer = ClaudeReviewer("test-key")
        self.assertEqual(reviewer.api_key, "test-key")

    def test_github_client_init(self):
        """Test that GitHubClient initializes correctly"""
        client = GitHubClient("test-token")
        self.assertEqual(client.token, "test-token")


if __name__ == '__main__':
    unittest.main()