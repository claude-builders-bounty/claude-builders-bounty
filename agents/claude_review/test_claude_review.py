#!/usr/bin/env python3

import unittest

import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).with_name("claude_review.py")
_MODULE_NAME = "claude_review_under_test"
_SPEC = importlib.util.spec_from_file_location(_MODULE_NAME, _MODULE_PATH)
assert _SPEC and _SPEC.loader
claude_review = importlib.util.module_from_spec(_SPEC)
sys.modules[_MODULE_NAME] = claude_review
_SPEC.loader.exec_module(claude_review)

PullRequest = claude_review.PullRequest
heuristic_review = claude_review.heuristic_review
parse_pr_url = claude_review.parse_pr_url
render_markdown = claude_review.render_markdown


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        owner, repo, number = parse_pr_url("https://github.com/acme/demo/pull/42")
        self.assertEqual(owner, "acme")
        self.assertEqual(repo, "demo")
        self.assertEqual(number, 42)

    def test_heuristic_review_sections(self) -> None:
        pr = PullRequest(
            owner="acme",
            repo="demo",
            number=1,
            title="Add auth middleware",
            body="Protect admin routes.",
            author="dev",
            base="main",
            head="feature/auth",
            additions=120,
            deletions=10,
            changed_files=3,
            is_draft=False,
            files=[{"path": "src/auth.ts", "additions": 120, "deletions": 10}],
            diff="console.log('debug')\n",
        )
        body = heuristic_review(pr)
        self.assertIn("## Summary of changes", body)
        self.assertIn("## Identified risks", body)
        self.assertIn("## Improvement suggestions", body)
        self.assertIn("## Confidence score", body)
        self.assertIn("auth", body.lower())

    def test_render_markdown_header(self) -> None:
        pr = PullRequest(
            owner="acme",
            repo="demo",
            number=7,
            title="Fix parser",
            body="",
            author="dev",
            base="main",
            head="fix/parser",
            additions=5,
            deletions=1,
            changed_files=1,
            is_draft=False,
            files=[],
            diff="",
        )
        rendered = render_markdown(pr, "## Summary of changes\nSmall fix.\n")
        self.assertIn("acme/demo#7", rendered)
        self.assertIn("Fix parser", rendered)


if __name__ == "__main__":
    unittest.main()
