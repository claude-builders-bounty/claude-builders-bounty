#!/usr/bin/env python3
"""Unit tests for the claude-review CLI."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest
from importlib.machinery import SourceFileLoader


CLI_PATH = pathlib.Path(__file__).resolve().parents[1] / "claude-review"
LOADER = SourceFileLoader("claude_review", str(CLI_PATH))
SPEC = importlib.util.spec_from_loader("claude_review", LOADER)
assert SPEC and SPEC.loader
claude_review = importlib.util.module_from_spec(SPEC)
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)


SAMPLE_DIFF = """\
diff --git a/src/auth/session.ts b/src/auth/session.ts
index 0000000..1111111 100644
--- a/src/auth/session.ts
+++ b/src/auth/session.ts
@@ -1,3 +1,7 @@
 export function getSession() {
-  return null
+  const token = process.env.API_TOKEN
+  if (!token) {
+    throw new Error("missing token")
+  }
+  return { token }
 }
diff --git a/README.md b/README.md
index 2222222..3333333 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Example
+Documented new session behavior.
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        parsed = claude_review.parse_pr_url("https://github.com/example/project/pull/42")
        self.assertEqual(parsed.owner, "example")
        self.assertEqual(parsed.repo, "project")
        self.assertEqual(parsed.number, 42)

    def test_parse_pr_url_rejects_non_pr_url(self) -> None:
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/example/project/issues/42")

    def test_parse_diff_counts_files_and_lines(self) -> None:
        analysis = claude_review.parse_diff(SAMPLE_DIFF)
        self.assertEqual(len(analysis.files), 2)
        self.assertEqual(analysis.total_additions, 6)
        self.assertEqual(analysis.total_deletions, 1)
        self.assertEqual(analysis.files[0].path, "src/auth/session.ts")

    def test_identifies_missing_tests_and_security_risk(self) -> None:
        analysis = claude_review.parse_diff(SAMPLE_DIFF)
        risks = claude_review.identify_risks(analysis)
        self.assertTrue(any("without matching test files" in risk for risk in risks))
        self.assertTrue(any("Auth, permission, or secret-handling" in risk for risk in risks))

    def test_rendered_review_has_required_sections(self) -> None:
        metadata = claude_review.PullRequestMetadata(
            title="Add session handling",
            author="octocat",
            base="main",
            head="session",
            additions=6,
            deletions=1,
            changed_files=2,
            html_url="https://github.com/example/project/pull/42",
        )
        review = claude_review.render_review(metadata, claude_review.parse_diff(SAMPLE_DIFF))
        self.assertIn("### Summary", review)
        self.assertIn("### Identified risks", review)
        self.assertIn("### Improvement suggestions", review)
        self.assertRegex(review, r"### Confidence score: (Low|Medium|High)")


if __name__ == "__main__":
    unittest.main()
