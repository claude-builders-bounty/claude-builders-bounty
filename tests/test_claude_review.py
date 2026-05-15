import importlib.util
import importlib.machinery
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "claude-review"
loader = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT))
spec = importlib.util.spec_from_loader("claude_review", loader)
claude_review = importlib.util.module_from_spec(spec)
sys.modules["claude_review"] = claude_review
assert spec.loader is not None
spec.loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/app/page.tsx b/app/page.tsx
index 0000000..1111111 100644
--- a/app/page.tsx
+++ b/app/page.tsx
@@ -1,2 +1,4 @@
-export default function Page() { return null }
+export default function Page() {
+  console.log(process.env.SECRET)
+  return null
+}
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/owner/repo/issues/123")

    def test_analyze_diff_extracts_stats_and_risks(self):
        stats = claude_review.analyze_diff(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["app/page.tsx"])
        self.assertEqual(stats.additions, 4)
        self.assertEqual(stats.deletions, 1)
        self.assertIn("credential or environment handling changed", stats.risk_hits)
        self.assertIn("confirm debug output is intentional and not noisy", stats.suggestion_hits)

    def test_format_review_has_required_sections(self):
        stats = claude_review.analyze_diff(SAMPLE_DIFF)
        review = claude_review.format_review("https://github.com/owner/repo/pull/123", stats)
        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertRegex(review, r"### Confidence: (Low|Medium|High)")


if __name__ == "__main__":
    unittest.main()
