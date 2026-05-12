import unittest
import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "agents" / "pr-reviewer" / "claude_review.py"
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = claude_review
SPEC.loader.exec_module(claude_review)

confidence = claude_review.confidence
parse_diff = claude_review.parse_diff
render_review = claude_review.render_review


SAMPLE_DIFF = """diff --git a/app/page.tsx b/app/page.tsx
index 1111111..2222222 100644
--- a/app/page.tsx
+++ b/app/page.tsx
@@ -1,2 +1,3 @@
 export default function Page() {
-  return null
+  return <main>Hello</main>
 }
"""


class PrReviewerTests(unittest.TestCase):
    def test_parses_basic_diff_stats(self):
        stats = parse_diff(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["app/page.tsx"])
        self.assertEqual(stats.additions, 1)
        self.assertEqual(stats.deletions, 1)
        self.assertEqual(confidence(stats), "High")

    def test_renders_required_sections(self):
        review = render_review("https://github.com/example/repo/pull/1", SAMPLE_DIFF)
        self.assertIn("## Summary", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertIn("## Confidence", review)


if __name__ == "__main__":
    unittest.main()
