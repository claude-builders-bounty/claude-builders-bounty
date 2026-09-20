import unittest

from claude_review import heuristic_review, parse_pr


class ReviewAgentTests(unittest.TestCase):
    def test_parse_pr_accepts_public_pull_request_url(self):
        self.assertEqual(parse_pr("https://github.com/acme/widgets/pull/42"), ("acme", "widgets", 42))

    def test_parse_pr_rejects_non_github_url(self):
        with self.assertRaises(ValueError):
            parse_pr("https://example.com/acme/widgets/pull/42")

    def test_heuristic_review_has_required_sections_and_risk(self):
        report = heuristic_review(
            "diff --git a/app.py b/app.py\n+rm -rf build\n",
            "acme",
            "widgets",
            42,
        )
        for section in ("## Summary", "## Identified risks", "## Improvement suggestions", "## Confidence"):
            self.assertIn(section, report)
        self.assertIn("Destructive operations", report)
        self.assertTrue(report.rstrip().endswith("Medium"))


if __name__ == "__main__":
    unittest.main()
