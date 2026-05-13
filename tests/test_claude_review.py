#!/usr/bin/env python3
"""Tests for the claude-review CLI."""

from __future__ import annotations

import unittest

from agents.pr_reviewer.claude_review import diff_stats, parse_pr_url, render_review


SAMPLE_DIFF = """diff --git a/src/auth/session.ts b/src/auth/session.ts
index 1111111..2222222 100644
--- a/src/auth/session.ts
+++ b/src/auth/session.ts
@@ -1,2 +1,3 @@
 export function getSession() {
+  return { userId: '123' }
 }
diff --git a/tests/session.test.ts b/tests/session.test.ts
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/session.test.ts
@@ -0,0 +1,3 @@
+test('session', () => {
+  expect(true).toBe(true)
+})
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        ref = parse_pr_url("https://github.com/example/project/pull/42")
        self.assertEqual(ref.owner, "example")
        self.assertEqual(ref.repo, "project")
        self.assertEqual(ref.number, 42)
        self.assertEqual(ref.diff_url, "https://github.com/example/project/pull/42.diff")

    def test_diff_stats(self) -> None:
        stats = diff_stats(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["src/auth/session.ts", "tests/session.test.ts"])
        self.assertEqual(stats.test_files, 1)
        self.assertGreater(stats.additions, 0)

    def test_render_review_contains_required_sections(self) -> None:
        ref = parse_pr_url("https://github.com/example/project/pull/42")
        review = render_review(ref, SAMPLE_DIFF)
        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertRegex(review, r"### Confidence: (Low|Medium|High)")


if __name__ == "__main__":
    unittest.main()
