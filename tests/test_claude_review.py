import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "agents" / "claude-review.py"
spec = importlib.util.spec_from_file_location("claude_review", SCRIPT)
review = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = review
spec.loader.exec_module(review)


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = review.parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual((ref.owner, ref.repo, ref.number), ("owner", "repo", "123"))

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            review.parse_pr_url("https://example.com/not/a/pr")

    def test_analyzes_risky_diff(self):
        diff = """diff --git a/script.sh b/script.sh
+++ b/script.sh
@@
+rm -rf build
+git status
-delete old
"""
        analysis = review.analyze_diff(diff)
        self.assertIn("script.sh", analysis["files"])
        self.assertIn("destructive shell command", analysis["risks"])
        self.assertEqual(analysis["confidence"], "Medium")

    def test_render_has_required_sections(self):
        markdown = review.render_review("https://github.com/o/r/pull/1", {
            "files": ["README.md"], "added": 3, "removed": 1,
            "risks": [], "suggestions": ["Check rendered Markdown."], "confidence": "High",
        })
        self.assertIn("## Summary", markdown)
        self.assertIn("## Identified risks", markdown)
        self.assertIn("## Improvement suggestions", markdown)
        self.assertIn("## Confidence: High", markdown)


if __name__ == "__main__":
    unittest.main()
