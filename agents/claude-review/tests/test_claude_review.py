from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "claude_review.py"
spec = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["claude_review"] = claude_review
spec.loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/src/auth/session.ts b/src/auth/session.ts
index 1111111..2222222 100644
--- a/src/auth/session.ts
+++ b/src/auth/session.ts
@@ -1,2 +1,4 @@
 export function canRead() {
+  // TODO: wire tenant check
+  return true
   return false
 }
diff --git a/src/projects/list.ts b/src/projects/list.ts
index 3333333..4444444 100644
--- a/src/projects/list.ts
+++ b/src/projects/list.ts
@@ -1,2 +1,3 @@
+export const query = "DELETE FROM projects"
 export const ok = true
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        pr = claude_review.parse_pr_url("https://github.com/example/repo/pull/42")
        self.assertEqual(pr.owner, "example")
        self.assertEqual(pr.repo, "repo")
        self.assertEqual(pr.number, 42)

    def test_parse_diff_stats(self) -> None:
        stats = claude_review.parse_diff(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["src/auth/session.ts", "src/projects/list.ts"])
        self.assertEqual(stats.additions, 3)
        self.assertEqual(stats.deletions, 0)
        self.assertEqual(stats.hunks, 2)

    def test_review_contains_required_sections_and_risks(self) -> None:
        pr = claude_review.PullRequest("example", "repo", 42, "Test PR")
        review = claude_review.render_review(pr, claude_review.parse_diff(SAMPLE_DIFF), SAMPLE_DIFF)
        self.assertIn("## Summary", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertIn("## Confidence", review)
        self.assertIn("Auth or permission-adjacent files changed", review)
        self.assertIn("Application code changed without obvious test files", review)
        self.assertIn("Potentially destructive SQL appears", review)


if __name__ == "__main__":
    unittest.main()
