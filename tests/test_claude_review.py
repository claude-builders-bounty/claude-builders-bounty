"""
Unit tests for Claude PR Reviewer Agent.
Tests URL parsing, diff analysis heuristics, CLI parsing, and Markdown output formatting.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add agent path to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_DIR = os.path.join(BASE_DIR, "agents", "claude-review")
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from github_client import parse_pr_url
from llm_providers import heuristic_review, format_markdown_review
from reviewer import ClaudeReviewer
from cli import build_parser


class TestClaudeReviewURLParsing(unittest.TestCase):
    """Tests for GitHub PR URL and reference parsing."""

    def test_standard_https_url(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/claude-builders/test-repo/pull/42")
        self.assertEqual(owner, "claude-builders")
        self.assertEqual(repo, "test-repo")
        self.assertEqual(pr_num, 42)

    def test_trailing_slash_and_params(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo/pull/101/files?diff=unified")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr_num, 101)

    def test_shorthand_reference(self):
        owner, repo, pr_num = parse_pr_url("octocat/Hello-World#77")
        self.assertEqual(owner, "octocat")
        self.assertEqual(repo, "Hello-World")
        self.assertEqual(pr_num, 77)

    def test_invalid_url_raises_error(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://example.com/not-github/pull/123")


class TestHeuristicAnalysis(unittest.TestCase):
    """Tests for static analysis and Markdown format compliance."""

    def test_detects_destructive_command(self):
        sample_diff = """
diff --git a/cleanup.sh b/cleanup.sh
--- a/cleanup.sh
+++ b/cleanup.sh
@@ -1,2 +1,3 @@
+rm -rf /tmp/build_cache/*
"""
        review = heuristic_review(sample_diff, pr_title="Add cleanup script")
        self.assertIn("### 📝 Summary of Changes", review)
        self.assertIn("### ⚠️ Identified Risks", review)
        self.assertIn("### 💡 Improvement Suggestions", review)
        self.assertIn("### 🎯 Confidence Score", review)
        self.assertIn("rm -rf", review)

    def test_detects_secrets(self):
        sample_diff = """
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
+api_key = "sk_live_1234567890abcdef12345"
"""
        review = heuristic_review(sample_diff, pr_title="Set production key")
        self.assertIn("Security Risk (Secrets)", review)

    def test_clean_safe_diff(self):
        sample_diff = """
diff --git a/tests/test_math.py b/tests/test_math.py
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -1,2 +1,4 @@
+def test_addition():
+    assert 1 + 1 == 2
"""
        review = heuristic_review(sample_diff, pr_title="Add math unit tests")
        self.assertIn("High", review)
        self.assertIn("Test Coverage Present", review)


class TestCLIParser(unittest.TestCase):
    """Tests for CLI flags and validation."""

    def setUp(self):
        self.parser = build_parser()

    def test_pr_argument(self):
        args = self.parser.parse_args(["--pr", "https://github.com/foo/bar/pull/1"])
        self.assertEqual(args.pr, "https://github.com/foo/bar/pull/1")
        self.assertIsNone(args.diff)

    def test_diff_argument(self):
        args = self.parser.parse_args(["--diff", "sample.patch", "--provider", "heuristic"])
        self.assertEqual(args.diff, "sample.patch")
        self.assertEqual(args.provider, "heuristic")

    def test_mutual_exclusion(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--pr", "https://github.com/a/b/pull/1", "--diff", "a.patch"])


class TestReviewerOrchestrator(unittest.TestCase):
    """Tests for review orchestrator flow."""

    @patch("reviewer.fetch_pr_diff")
    @patch("reviewer.fetch_pr_metadata")
    def test_reviewer_flow(self, mock_meta, mock_diff):
        mock_diff.return_value = "diff --git a/file.py b/file.py\n+print('hello')"
        mock_meta.return_value = {"title": "Say hello", "body": "Simple greeting PR"}

        reviewer = ClaudeReviewer(provider="heuristic")
        markdown, comment_url = reviewer.review_pr("https://github.com/test/repo/pull/10", post_comment=False)

        self.assertIn("### 📝 Summary of Changes", markdown)
        self.assertIn("### 🎯 Confidence Score", markdown)
        self.assertIsNone(comment_url)


if __name__ == "__main__":
    unittest.main()
