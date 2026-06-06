#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import claude_review  # noqa: E402


class ParsePrUrlTests(unittest.TestCase):
    def test_full_url(self):
        owner, repo, number = claude_review.parse_pr_url(
            "https://github.com/acme/widgets/pull/42"
        )
        self.assertEqual((owner, repo, number), ("acme", "widgets", 42))

    def test_number_only(self):
        owner, repo, number = claude_review.parse_pr_url("42")
        self.assertEqual((owner, repo, number), (None, None, 42))

    def test_invalid_url(self):
        owner, repo, number = claude_review.parse_pr_url("not-a-pr")
        self.assertEqual((owner, repo, number), (None, None, None))


class AnalyzePrTests(unittest.TestCase):
    def _metadata(self, **overrides):
        base = {
            "title": "Add widget endpoint",
            "body": "Implements the widget API described in issue #12.",
            "changed_files": [
                {
                    "filename": "src/widget.py",
                    "status": "modified",
                    "additions": 40,
                    "deletions": 2,
                    "changes": 42,
                }
            ],
            "total_changes": 42,
            "commits": 1,
            "additions": 40,
            "deletions": 2,
            "labels": [],
        }
        base.update(overrides)
        return base

    def test_narrative_summary_includes_title_and_body(self):
        review = claude_review.analyze_pr(self._metadata(), diff="+++ b/src/widget.py\n+pass\n")
        self.assertIn("Add widget endpoint", review["summary"])
        self.assertIn("widget API", review["summary"])

    def test_detects_todo_markers(self):
        diff = "+++ b/app.py\n+# TODO: handle edge case\n"
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertTrue(any("TODO" in risk for risk in review["risks"]))

    def test_cli_print_not_flagged_as_debug(self):
        diff = (
            "+++ b/cli.py\n"
            "+print(final_content)\n"
            "+print(f\"Wrote {output_path}\")\n"
        )
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertFalse(any("Debug/console" in risk for risk in review["risks"]))

    def test_debug_print_flagged(self):
        diff = "+++ b/app.py\n+print('debug state:', value)\n"
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertTrue(any("Debug/console" in risk for risk in review["risks"]))

    def test_large_pr_lowers_confidence(self):
        metadata = self._metadata(total_changes=1200, changed_files=[{"filename": f"f{i}.py", "status": "added", "additions": 100, "deletions": 0, "changes": 100} for i in range(20)])
        review = claude_review.analyze_pr(metadata, diff="+line\n" * 1200)
        self.assertEqual(review["confidence"], "Low")


class SummaryFormatTests(unittest.TestCase):
    def test_summary_has_blank_line_before_file_breakdown(self):
        metadata = {
            "title": "Add feature",
            "body": "Implements the feature.",
            "changed_files": [
                {
                    "filename": "src/app.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 1,
                    "changes": 11,
                }
            ],
            "total_changes": 11,
            "commits": 1,
            "additions": 10,
            "deletions": 1,
            "labels": [],
        }
        review = claude_review.analyze_pr(metadata, diff="+++ b/src/app.py\n+pass\n")
        self.assertIn("feature.\n\n**File type breakdown:**", review["summary"])


class MarkdownFormatTests(unittest.TestCase):
    def test_required_sections_present(self):
        metadata = {
            "title": "Test PR",
            "author": "alice",
            "owner": "acme",
            "repo": "widgets",
            "pr_number": 7,
            "changed_files": [],
            "additions": 1,
            "deletions": 0,
            "total_changes": 1,
            "commits": 1,
            "base_branch": "main",
            "head_branch": "feature",
            "labels": [],
        }
        review = {
            "summary": "Updates one file.",
            "risks": ["No significant risks identified."],
            "suggestions": ["No additional suggestions."],
            "confidence": "High",
        }
        md = claude_review.format_markdown(metadata, review)
        self.assertIn("### Summary of Changes", md)
        self.assertIn("### Identified Risks", md)
        self.assertIn("### Improvement Suggestions", md)
        self.assertIn("### Confidence Score: **High**", md)


if __name__ == "__main__":
    unittest.main()
