#!/usr/bin/env python3
from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import sys
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "bin" / "claude-review"
LOADER = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT))
SPEC = importlib.util.spec_from_loader("claude_review", LOADER)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules["claude_review"] = module
SPEC.loader.exec_module(module)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        ref = module.parse_pr_url("https://github.com/example/project/pull/123")
        self.assertEqual(ref.owner, "example")
        self.assertEqual(ref.repo, "project")
        self.assertEqual(ref.number, 123)

    def test_changed_files(self) -> None:
        diff = "diff --git a/app/page.tsx b/app/page.tsx\n+hello\n-old\n"
        self.assertEqual(module.changed_files(diff), ["app/page.tsx"])
        self.assertEqual(module.count_changed_lines(diff), (1, 1))

    def test_offline_review_shape(self) -> None:
        stats = module.classify_files(["app/page.tsx"], additions=10, deletions=2)
        review = module.offline_review({"title": "Update dashboard"}, stats)
        self.assertIn("## Summary", review)
        self.assertIn("## Identified risks", review)
        self.assertIn("## Improvement suggestions", review)
        self.assertIn("## Confidence", review)


if __name__ == "__main__":
    unittest.main()
