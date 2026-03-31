import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from review_agent.claude_review import (
    PullRequestRef,
    build_review_markdown,
    heuristically_review_pull_request,
    main,
    parse_pr_url,
)


class PullRequestReviewAgentTests(unittest.TestCase):
    def test_parse_pr_url_extracts_owner_repo_and_number(self):
        ref = parse_pr_url("https://github.com/octo/demo/pull/123")
        self.assertEqual(ref, PullRequestRef(owner="octo", repo="demo", number=123))

    def test_markdown_output_has_required_sections(self):
        markdown = build_review_markdown(
            summary=[
                "Adds a CLI wrapper that fetches a pull request diff and generates a review.",
                "Includes a fallback heuristic path when Claude Code is unavailable.",
            ],
            risks=["Network failures can prevent fetching diff content."],
            suggestions=["Cache GitHub responses for repeated local runs."],
            confidence="Medium",
        )

        self.assertIn("## Summary", markdown)
        self.assertIn("## Risks", markdown)
        self.assertIn("## Improvement Suggestions", markdown)
        self.assertIn("## Confidence", markdown)
        self.assertIn("- Network failures can prevent fetching diff content.", markdown)

    def test_heuristic_review_finds_risks_from_diff(self):
        review = heuristically_review_pull_request(
            title="Add force push helper",
            body="This PR updates release automation.",
            diff_text="""
diff --git a/scripts/release.sh b/scripts/release.sh
+git push --force origin main
diff --git a/.github/workflows/release.yml b/.github/workflows/release.yml
+secrets: inherit
""".strip(),
        )

        self.assertTrue(review.summary)
        self.assertTrue(any("force" in risk.lower() for risk in review.risks))
        self.assertIn(review.confidence, {"Low", "Medium", "High"})

    def test_cli_writes_markdown_review(self):
        fake_fetcher = Mock(
            return_value={
                "title": "Add safer release checks",
                "body": "Tightens release automation.",
                "diff": "diff --git a/release.sh b/release.sh\n+echo done\n",
            }
        )

        stdout = io.StringIO()
        exit_code = main(
            argv=["--pr", "https://github.com/octo/demo/pull/9"],
            stdout=stdout,
            fetcher=fake_fetcher,
        )

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("## Summary", output)
        self.assertIn("## Confidence", output)
        fake_fetcher.assert_called_once()

    def test_cli_can_save_output_file(self):
        fake_fetcher = Mock(
            return_value={
                "title": "Adjust parser",
                "body": "Minor parser changes.",
                "diff": "diff --git a/parser.py b/parser.py\n+return True\n",
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "review.md"
            exit_code = main(
                argv=[
                    "--pr",
                    "https://github.com/octo/demo/pull/10",
                    "--output",
                    str(output_path),
                ],
                stdout=io.StringIO(),
                fetcher=fake_fetcher,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertIn("## Summary", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
