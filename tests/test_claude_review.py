import unittest

import importlib.machinery
import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "bin" / "claude-review"
LOADER = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT_PATH))
SPEC = importlib.util.spec_from_loader("claude_review", LOADER)
claude_review = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)


class ClaudeReviewTests(unittest.TestCase):
    def test_parses_full_pr_url(self):
        self.assertEqual(
            claude_review.parse_pr("https://github.com/org/repo/pull/123"),
            ("org", "repo", 123),
        )

    def test_parses_owner_repo_shorthand(self):
        self.assertEqual(claude_review.parse_pr("org/repo#456"), ("org", "repo", 456))

    def test_detects_risky_diff_without_tests(self):
        pr = claude_review.PullRequest(
            owner="org",
            repo="repo",
            number=1,
            title="Add migration",
            body="",
            changed_files=1,
            additions=4,
            deletions=0,
            diff="diff --git a/app/db.py b/app/db.py\n+DROP TABLE users\n",
        )

        review = claude_review.fallback_review(pr)

        self.assertIn("## Summary", review)
        self.assertIn("Data or schema mutation", review)
        self.assertIn("No obvious test file changed", review)
        self.assertIn("## Confidence: Medium", review)


if __name__ == "__main__":
    unittest.main()
