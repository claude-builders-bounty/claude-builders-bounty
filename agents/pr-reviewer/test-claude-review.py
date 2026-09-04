#!/usr/bin/env python3
"""Unit tests for claude-review.py."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "claude_review",
    Path(__file__).with_name("claude-review.py"),
)
claude_review = importlib.util.module_from_spec(SPEC)
claude_review.__name__ = "claude_review"
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)  # type: ignore[union-attr]


class TestParsePRUrl(unittest.TestCase):
    def test_full_url(self):
        info = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(info.owner, "owner")
        self.assertEqual(info.repo, "repo")
        self.assertEqual(info.number, 123)

    def test_short_form(self):
        info = claude_review.parse_pr_url("owner/repo/456")
        self.assertEqual(info.number, 456)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("not-a-url")


class TestCountChanges(unittest.TestCase):
    def test_counts(self):
        diff = """diff --git a/file.txt b/file.txt
index abc..def 100644
--- a/file.txt
+++ b/file.txt
@@ -1 +1,2 @@
- old
+new1
+new2
"""
        files, additions, deletions = claude_review.count_changes(diff)
        self.assertEqual(files, 1)
        self.assertEqual(additions, 2)
        self.assertEqual(deletions, 1)


class TestRuleBasedReview(unittest.TestCase):
    def test_detects_risk(self):
        diff = "diff --git a/x.sh b/x.sh\n+rm -rf /\n"
        pr = {"title": "cleanup", "body": ""}
        review = claude_review.rule_based_review(diff, pr)
        self.assertIn("rm -rf", review)
        self.assertIn("Confidence Score", review)

    def test_high_confidence_safe(self):
        diff = "diff --git a/README.md b/README.md\n+hello world\n"
        pr = {"title": "docs", "body": "Update readme"}
        review = claude_review.rule_based_review(diff, pr)
        self.assertIn("High", review)


if __name__ == "__main__":
    unittest.main()
