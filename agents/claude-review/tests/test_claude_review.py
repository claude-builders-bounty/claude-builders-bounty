#!/usr/bin/env python3
import json
import sys
import unittest
import unittest.mock
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

    def test_sanitize_pr_body_strips_claim_commands(self):
        body = "/claim #1\n## Summary\nAdds a changelog generator."
        self.assertEqual(
            claude_review.sanitize_pr_body(body),
            "Adds a changelog generator.",
        )

    def test_sanitize_pr_body_extracts_description_section_only(self):
        body = (
            "### Description\n"
            "This PR adds a widget API.\n"
            "### What has been done\n"
            "- Added endpoint\n"
            "- Added tests"
        )
        self.assertEqual(
            claude_review.sanitize_pr_body(body),
            "This PR adds a widget API.",
        )

    def test_sanitize_pr_body_stops_at_included_section(self):
        body = (
            "/claim #1\n"
            "## Summary\nAdds a changelog generator.\n"
            "## Included\n- Skill documentation\n- Python generator"
        )
        self.assertEqual(
            claude_review.sanitize_pr_body(body),
            "Adds a changelog generator.",
        )

    def test_sanitize_pr_body_handles_colon_summary_block(self):
        body = (
            "Closes #7\n\n"
            "Summary:\n"
            "- Add a toast component.\n"
            "- Style with tokens.\n\n"
            "Verification:\n"
            "- Parsed HTML pages."
        )
        self.assertEqual(
            claude_review.sanitize_pr_body(body),
            "Add a toast component. Style with tokens.",
        )

    def test_single_file_type_skips_cross_language_suggestion(self):
        review = claude_review.analyze_pr(self._metadata(), diff="+++ b/src/widget.py\n+pass\n")
        self.assertFalse(
            any("file types" in suggestion for suggestion in review["suggestions"])
        )

    def test_docs_and_images_skip_cross_language_suggestion(self):
        metadata = self._metadata(
            changed_files=[
                {"filename": "README.md", "status": "modified", "additions": 21, "deletions": 0, "changes": 21},
                {"filename": "demo.png", "status": "added", "additions": 0, "deletions": 0, "changes": 0},
                {"filename": "hooks/pre-tool-use.py", "status": "added", "additions": 131, "deletions": 0, "changes": 131},
            ],
            total_changes=152,
            additions=152,
            commits=2,
        )
        review = claude_review.analyze_pr(metadata, diff="+++ b/hooks/pre-tool-use.py\n+pass\n")
        self.assertFalse(
            any("cross-language" in suggestion for suggestion in review["suggestions"])
        )

    def test_multiple_code_extensions_trigger_cross_language_suggestion(self):
        metadata = self._metadata(
            changed_files=[
                {"filename": "src/app.py", "status": "modified", "additions": 10, "deletions": 1, "changes": 11},
                {"filename": "src/app.ts", "status": "modified", "additions": 8, "deletions": 2, "changes": 10},
            ],
            total_changes=21,
            additions=18,
            deletions=3,
        )
        review = claude_review.analyze_pr(metadata, diff="+++ b/src/app.py\n+pass\n+++ b/src/app.ts\n+pass\n")
        self.assertTrue(
            any("cross-language" in suggestion for suggestion in review["suggestions"])
        )

    def test_detects_todo_markers(self):
        diff = "+++ b/app.py\n+# TODO: handle edge case\n"
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertTrue(any("TODO" in message for _, message in review["risks"]))

    def test_risks_include_severity_tags(self):
        diff = "+++ b/app.py\n+api_key = 'supersecretvalue123'\n"
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertTrue(any(severity == "high" for severity, _ in review["risks"]))

    def test_cli_print_not_flagged_as_debug(self):
        diff = (
            "+++ b/cli.py\n"
            "+print(final_content)\n"
            "+print(f\"Wrote {output_path}\")\n"
        )
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertFalse(any("Debug/console" in message for _, message in review["risks"]))

    def test_debug_print_flagged(self):
        diff = "+++ b/app.py\n+print('debug state:', value)\n"
        review = claude_review.analyze_pr(self._metadata(), diff=diff)
        self.assertTrue(any("Debug/console" in message for _, message in review["risks"]))

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


class CliFlagTests(unittest.TestCase):
    def test_diff_alias_sets_diff_only(self):
        with unittest.mock.patch("sys.argv", ["claude-review", "--pr", "42", "--diff"]):
            args = claude_review.parse_args()
        self.assertTrue(args.diff_only)
        self.assertFalse(args.post)

    def test_post_comment_alias_sets_post(self):
        with unittest.mock.patch("sys.argv", ["claude-review", "--pr", "42", "--post-comment"]):
            args = claude_review.parse_args()
        self.assertTrue(args.post)
        self.assertFalse(args.diff_only)


class PostReviewCommentTests(unittest.TestCase):
    def test_post_review_comment_posts_json_payload(self):
        captured = {}

        class FakeResponse:
            def read(self):
                return b'{"html_url":"https://github.com/acme/widgets/pull/7#issuecomment-1"}'

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(req, timeout=30):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["body"] = json.loads(req.data.decode())
            return FakeResponse()

        with unittest.mock.patch("claude_review.urllib.request.urlopen", fake_urlopen):
            claude_review.post_review_comment(
                "acme",
                "widgets",
                7,
                "## Review\n\nLooks good.",
                "ghp_test",
            )

        self.assertIn("/repos/acme/widgets/issues/7/comments", captured["url"])
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["body"]["body"], "## Review\n\nLooks good.")


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
            "risks": [("low", "No significant risks identified.")],
            "suggestions": ["No additional suggestions."],
            "confidence": "High",
        }
        md = claude_review.format_markdown(metadata, review)
        self.assertIn("### Summary of Changes", md)
        self.assertIn("### Identified Risks", md)
        self.assertIn("**[LOW]** No significant risks identified.", md)
        self.assertIn("### Improvement Suggestions", md)
        self.assertIn("### Confidence Score: **High**", md)


if __name__ == "__main__":
    unittest.main()
