#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import claude_review  # noqa: E402


class ParsePrUrlTests(unittest.TestCase):
    def test_valid_url(self):
        owner, repo, number = claude_review.parse_pr_url(
            "https://github.com/acme/widgets/pull/42"
        )
        self.assertEqual((owner, repo, number), ("acme", "widgets", "42"))

    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://gitlab.com/acme/widgets/-/merge_requests/1")


class StaticAnalysisTests(unittest.TestCase):
    def _pr(self, diff: str, title: str = "Test PR", body: str = "") -> claude_review.PullRequest:
        return claude_review.PullRequest("acme", "widgets", "1", title, body, diff)

    def test_detects_hardcoded_secret(self):
        diff = "+++ b/app.py\n+api_key = 'sk-live-abc123'\n"
        review = claude_review.analyze_static(self._pr(diff))
        self.assertTrue(any("secret" in risk.lower() for risk in review.risks))

    def test_detects_large_pr(self):
        lines = "\n".join(f"+line {i}" for i in range(501))
        review = claude_review.analyze_static(self._pr(lines))
        self.assertTrue(any("large pr" in risk.lower() for risk in review.risks))

    def test_clean_diff_gets_medium_confidence(self):
        diff = "+++ b/README.md\n+Hello world\n"
        review = claude_review.analyze_static(self._pr(diff, body="Docs update"))
        self.assertEqual(review.confidence, "Medium")
        self.assertIn("Docs update", review.summary)


class MarkdownFormatTests(unittest.TestCase):
    def test_required_sections_present(self):
        review = claude_review.Review(
            summary="Adds a new endpoint.",
            risks=["Missing input validation."],
            suggestions=["Add unit tests."],
            confidence="High",
        )
        md = claude_review.format_markdown(review)
        self.assertIn("### Summary of Changes", md)
        self.assertIn("### Identified Risks", md)
        self.assertIn("### Improvement Suggestions", md)
        self.assertIn("### Confidence Score: **High**", md)
        self.assertIn("- Missing input validation.", md)


class ConfidenceNormalizationTests(unittest.TestCase):
    def test_normalize_levels(self):
        self.assertEqual(claude_review._normalize_confidence("High confidence"), "High")
        self.assertEqual(claude_review._normalize_confidence("low"), "Low")
        self.assertEqual(claude_review._normalize_confidence("unknown"), "Medium")


if __name__ == "__main__":
    unittest.main()
