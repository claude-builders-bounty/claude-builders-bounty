"""Unit tests for claude-review (no network, no API key needed)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claude_review.analyzer import ReviewResult, _parse_json, review_diff
from claude_review.github_client import GitHubClient


class TestParseJson(unittest.TestCase):
    def test_plain_json(self):
        d = _parse_json('{"summary": "ok", "risks": [], "suggestions": [], "confidence": "High"}')
        self.assertEqual(d["summary"], "ok")

    def test_fenced_json(self):
        d = _parse_json('```json\n{"summary": "s", "risks": ["a"], "suggestions": [], "confidence": "Low"}\n```')
        self.assertEqual(d["risks"], ["a"])

    def test_trailing_prose(self):
        d = _parse_json('{"summary": "s", "risks": [], "suggestions": [], "confidence": "Medium"}\n\nDone!')
        self.assertEqual(d["confidence"], "Medium")


class TestReviewResult(unittest.TestCase):
    def test_to_markdown_full(self):
        r = ReviewResult(
            summary="Adds login flow",
            risks=["[HIGH] race", "[LOW] magic number"],
            suggestions=["add lock"],
            confidence="High",
        )
        md = r.to_markdown("https://github.com/a/b/pull/1", "Fix login")
        self.assertIn("**PR:**", md)
        self.assertIn("[HIGH] race", md)
        self.assertIn("**Confidence:** High", md)

    def test_to_markdown_error(self):
        r = ReviewResult(error="TimeoutError: x")
        self.assertIn("Review failed", r.to_markdown())

    def test_review_diff_without_key_returns_error(self):
        # no API key in env -> must return error result, not raise
        import os
        saved = {k: os.environ.pop(k, None) for k in ("DEEPSEEK_API_KEY", "CLAUDE_REVIEW_API_KEY")}
        try:
            r = review_diff("diff --git a/x.py b/x.py\n+print(1)\n")
            self.assertTrue(r.error)
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v


class TestGitHubClient(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            GitHubClient.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner/repo", "123"),
        )

    def test_parse_pr_url_extra_segments(self):
        self.assertEqual(
            GitHubClient.parse_pr_url("https://github.com/owner/repo/pull/123/files"),
            ("owner/repo", "123"),
        )

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            GitHubClient.parse_pr_url("https://example.com/not-a-pr")


if __name__ == "__main__":
    unittest.main()
