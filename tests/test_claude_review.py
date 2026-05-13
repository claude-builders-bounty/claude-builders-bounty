#!/usr/bin/env python3
"""Regression tests for the structured PR review agent."""
from __future__ import annotations

import pathlib
import runpy
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "claude-review"

module_globals = runpy.run_path(str(MODULE_PATH))
claude_review = SimpleNamespace(**module_globals)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url_accepts_canonical_github_url(self) -> None:
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/example/project/pull/42"),
            ("example", "project", 42),
        )

    def test_parse_pr_url_rejects_invalid_url(self) -> None:
        with self.assertRaises(SystemExit):
            claude_review.parse_pr_url("https://github.com/example/project/issues/42")

    def test_agent_definition_documents_cli_usage(self) -> None:
        agent = (ROOT / ".claude" / "agents" / "pr-reviewer.md").read_text(encoding="utf-8")

        self.assertIn("name: pr-reviewer", agent)
        self.assertIn("python3 claude-review --pr", agent)
        self.assertIn("Summary of changes", agent)
        self.assertIn("Confidence score", agent)

    def test_workflow_uses_minimum_comment_permissions(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "claude-review.yml").read_text(encoding="utf-8")

        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("pull-requests: read", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_build_review_includes_required_sections_and_confidence(self) -> None:
        pr = {
            "title": "Add workflow automation",
            "additions": 25,
            "deletions": 4,
        }
        files = [
            claude_review.FileChange(
                filename=".github/workflows/review.yml",
                additions=20,
                deletions=1,
                status="modified",
                patch="+token: ${{ secrets.GITHUB_TOKEN }}",
            ),
            claude_review.FileChange(
                filename="tests/test_review.py",
                additions=5,
                deletions=3,
                status="added",
                patch="+def test_review(): pass",
            ),
        ]

        original_fetch_pr = claude_review.build_review.__globals__["fetch_pr"]
        claude_review.build_review.__globals__["fetch_pr"] = mock.Mock(return_value=(pr, files))
        try:
            review = claude_review.build_review("https://github.com/example/project/pull/42")
        finally:
            claude_review.build_review.__globals__["fetch_pr"] = original_fetch_pr

        self.assertIn("## Claude PR Review", review)
        self.assertIn("### Summary of changes", review)
        self.assertIn("### Identified risks", review)
        self.assertIn("### Improvement suggestions", review)
        self.assertIn("### Confidence score", review)
        self.assertIn("Workflow or CI changes", review)
        self.assertIn("credential-related terms", review)
        self.assertRegex(review, r"\*\*(Low|Medium|High)\*\*")

    def test_review_comment_includes_marker_for_idempotent_updates(self) -> None:
        pr = {"title": "Docs", "additions": 3, "deletions": 1}
        files = [
            claude_review.FileChange(
                filename="README.md",
                additions=3,
                deletions=1,
                status="modified",
                patch="+usage",
            )
        ]

        original_fetch_pr = claude_review.build_review.__globals__["fetch_pr"]
        claude_review.build_review.__globals__["fetch_pr"] = mock.Mock(return_value=(pr, files))
        try:
            review = claude_review.build_review("https://github.com/example/project/pull/42")
        finally:
            claude_review.build_review.__globals__["fetch_pr"] = original_fetch_pr

        self.assertTrue(review.startswith("<!-- claude-review-agent -->"))

    def test_post_pr_comment_updates_existing_agent_comment(self) -> None:
        calls: list[tuple[str, str, bytes | None]] = []

        def fake_github_request(url: str, *, method: str = "GET", data: bytes | None = None):
            calls.append((url, method, data))
            if method == "GET":
                return [
                    {"body": "human comment", "url": "https://api.github.com/comments/1"},
                    {
                        "body": "<!-- claude-review-agent -->\nold review",
                        "url": "https://api.github.com/comments/2",
                    },
                ]
            return None

        original_request = claude_review.post_pr_comment.__globals__["github_request"]
        original_token = claude_review.os.environ.get("GITHUB_TOKEN")
        claude_review.post_pr_comment.__globals__["github_request"] = fake_github_request
        claude_review.os.environ["GITHUB_TOKEN"] = "test-token"
        try:
            claude_review.post_pr_comment("owner", "repo", 7, "<!-- claude-review-agent -->\nnew review")
        finally:
            claude_review.post_pr_comment.__globals__["github_request"] = original_request
            if original_token is None:
                claude_review.os.environ.pop("GITHUB_TOKEN", None)
            else:
                claude_review.os.environ["GITHUB_TOKEN"] = original_token

        self.assertEqual(calls[0][1], "GET")
        self.assertEqual(calls[1][0], "https://api.github.com/comments/2")
        self.assertEqual(calls[1][1], "PATCH")

    def test_post_pr_comment_creates_when_no_marker_exists(self) -> None:
        calls: list[tuple[str, str, bytes | None]] = []

        def fake_github_request(url: str, *, method: str = "GET", data: bytes | None = None):
            calls.append((url, method, data))
            return [] if method == "GET" else None

        original_request = claude_review.post_pr_comment.__globals__["github_request"]
        original_token = claude_review.os.environ.get("GITHUB_TOKEN")
        claude_review.post_pr_comment.__globals__["github_request"] = fake_github_request
        claude_review.os.environ["GITHUB_TOKEN"] = "test-token"
        try:
            claude_review.post_pr_comment("owner", "repo", 7, "<!-- claude-review-agent -->\nnew review")
        finally:
            claude_review.post_pr_comment.__globals__["github_request"] = original_request
            if original_token is None:
                claude_review.os.environ.pop("GITHUB_TOKEN", None)
            else:
                claude_review.os.environ["GITHUB_TOKEN"] = original_token

        self.assertEqual(calls[1][1], "POST")
        self.assertTrue(calls[1][0].endswith("/repos/owner/repo/issues/7/comments"))


if __name__ == "__main__":
    unittest.main()
