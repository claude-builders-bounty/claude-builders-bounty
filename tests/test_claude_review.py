#!/usr/bin/env python3
from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("claude_review", str(ROOT / "bin" / "claude-review"))
SPEC = importlib.util.spec_from_loader("claude_review", LOADER)
claude_review = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        pr = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(pr.full_name, "owner/repo")
        self.assertEqual(pr.number, "123")

    def test_render_review_contains_required_sections(self) -> None:
        metadata = {
            "title": "Add CLI",
            "additions": 120,
            "deletions": 8,
            "changedFiles": 3,
            "files": [
                {"path": "bin/claude-review"},
                {"path": "tests/test_claude_review.py"},
                {"path": ".github/workflows/claude-review.yml"},
            ],
        }
        rendered = claude_review.render_review(metadata, "subprocess.run(['gh'])")
        self.assertIn("## Summary", rendered)
        self.assertIn("## Identified Risks", rendered)
        self.assertIn("## Improvement Suggestions", rendered)
        self.assertIn("## Confidence", rendered)
        self.assertIn("High", rendered)
        self.assertIn("Workflow changes", rendered)

    def test_no_tests_lowers_confidence(self) -> None:
        metadata = {
            "title": "Change docs",
            "additions": 20,
            "deletions": 1,
            "changedFiles": 1,
            "files": [{"path": "README.md"}],
        }
        rendered = claude_review.render_review(metadata, "diff")
        self.assertIn("No test or sample validation file", rendered)
        self.assertIn("Medium", rendered)

    def test_sqlite_in_filename_is_not_database_path(self) -> None:
        metadata = {
            "title": "Add template",
            "additions": 20,
            "deletions": 1,
            "changedFiles": 1,
            "files": [{"path": "tests/validate-nextjs-sqlite-template.sh"}],
        }
        rendered = claude_review.render_review(metadata, "diff")
        self.assertNotIn("Database or migration changes", rendered)


if __name__ == "__main__":
    unittest.main()
