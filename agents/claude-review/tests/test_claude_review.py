#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error
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


class TruncateSnippetTests(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(claude_review._truncate_snippet("Short text."), "Short text.")

    def test_long_text_truncates_at_word_boundary(self):
        text = (
            "This PR implements a python-based PreToolUse hooks gatekeeper that "
            "intercepts and blocks dangerous bash commands (e.g. rm -rf, DROP TABLE, "
            "git push --force, TRUNCATE, and DELETE FROM without a WHERE clause)."
        )
        snippet = claude_review._truncate_snippet(text, max_len=200)
        self.assertLessEqual(len(snippet), 203)
        self.assertTrue(snippet.endswith("..."))
        self.assertNotIn("TRUNCATE, and.", snippet)


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

        with unittest.mock.patch(
            "claude_review.find_existing_review_comment", return_value=None
        ), unittest.mock.patch("claude_review.urllib.request.urlopen", fake_urlopen):
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

    def test_post_review_comment_updates_existing_comment(self):
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

        with unittest.mock.patch(
            "claude_review.find_existing_review_comment", return_value=999
        ), unittest.mock.patch("claude_review.urllib.request.urlopen", fake_urlopen):
            claude_review.post_review_comment(
                "acme",
                "widgets",
                7,
                f"## Review\n\n{claude_review.REVIEW_MARKER}",
                "ghp_test",
            )

        self.assertIn("/repos/acme/widgets/issues/comments/999", captured["url"])
        self.assertEqual(captured["method"], "PATCH")

    def test_find_existing_review_comment_returns_matching_id(self):
        comments = [
            {"id": 1, "body": "Looks good to me."},
            {"id": 2, "body": f"## Review\n\n{claude_review.REVIEW_MARKER}"},
        ]
        with unittest.mock.patch("claude_review.gh_api", return_value=comments):
            comment_id = claude_review.find_existing_review_comment(
                "acme", "widgets", 7, "ghp_test"
            )
        self.assertEqual(comment_id, 2)


class SecurityRiskTests(unittest.TestCase):
    def _metadata(self, **overrides):
        base = {
            "title": "Security-sensitive change",
            "body": "",
            "changed_files": [],
            "total_changes": 10,
            "commits": 1,
            "additions": 10,
            "deletions": 0,
            "labels": [],
        }
        base.update(overrides)
        return base

    def test_flags_eval_in_diff(self):
        diff = "+result = eval(user_input)\n"
        review = claude_review.analyze_pr(self._metadata(), diff)
        messages = [risk for _, risk in review["risks"]]
        self.assertTrue(any("eval" in msg.lower() for msg in messages))

    def test_flags_sensitive_env_file_changes(self):
        metadata = self._metadata(
            changed_files=[
                {
                    "filename": ".env.production",
                    "status": "modified",
                    "additions": 2,
                    "deletions": 0,
                    "changes": 2,
                }
            ]
        )
        review = claude_review.analyze_pr(metadata, "")
        messages = [risk for _, risk in review["risks"]]
        self.assertTrue(any(".env.production" in msg for msg in messages))


class MaxFilesTests(unittest.TestCase):
    def test_filter_diff_by_filenames_keeps_only_selected_hunks(self):
        diff = (
            "diff --git a/src/a.py b/src/a.py\n"
            "+++ b/src/a.py\n"
            "+eval(user_input)\n"
            "diff --git a/src/b.py b/src/b.py\n"
            "+++ b/src/b.py\n"
            "+print('safe')\n"
        )
        filtered = claude_review.filter_diff_by_filenames(diff, {"src/a.py"})
        self.assertIn("src/a.py", filtered)
        self.assertNotIn("src/b.py", filtered)

    def test_truncates_changed_files_when_max_files_set(self):
        metadata = {
            "title": "Big refactor",
            "body": "",
            "changed_files": [
                {"filename": f"src/{i}.py", "status": "modified", "additions": 1, "deletions": 0, "changes": 1}
                for i in range(5)
            ],
            "total_changes": 5,
            "commits": 1,
            "additions": 5,
            "deletions": 0,
            "labels": [],
            "files_truncated": 3,
        }
        metadata["changed_files"] = metadata["changed_files"][:2]
        review = claude_review.analyze_pr(metadata, "")
        self.assertIn("2 of 5 file(s)", review["summary"])


class DiffFileTests(unittest.TestCase):
    SAMPLE_DIFF = """diff --git a/src/widget.py b/src/widget.py
new file mode 100644
--- /dev/null
+++ b/src/widget.py
@@ -0,0 +1,2 @@
+def widget():
+    pass
"""

    def test_parse_diff_filenames(self):
        files = claude_review.parse_diff_filenames(self.SAMPLE_DIFF)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["filename"], "src/widget.py")
        self.assertEqual(files[0]["status"], "added")
        self.assertEqual(files[0]["additions"], 2)

    def test_metadata_from_diff(self):
        metadata = claude_review.metadata_from_diff(
            self.SAMPLE_DIFF,
            title="Add widget",
            author="alice",
        )
        self.assertEqual(metadata["title"], "Add widget")
        self.assertEqual(metadata["author"], "alice")
        self.assertEqual(len(metadata["changed_files"]), 1)

    def test_src_without_tests_triggers_suggestion(self):
        metadata = claude_review.metadata_from_diff(
            self.SAMPLE_DIFF,
            title="Add widget",
            author="alice",
        )
        review = claude_review.analyze_pr(metadata, self.SAMPLE_DIFF)
        self.assertTrue(
            any("test" in suggestion.lower() for suggestion in review["suggestions"])
        )

    def test_diff_file_mode_does_not_require_pr(self):
        with unittest.mock.patch("sys.argv", ["claude-review", "--diff-file", "changes.diff"]):
            args = claude_review.parse_args()
        self.assertEqual(args.diff_file, "changes.diff")
        self.assertIsNone(args.pr)


class DiffFilterTests(unittest.TestCase):
    def test_filter_diff_excludes_test_and_doc_hunks(self):
        diff = (
            "diff --git a/README.md b/README.md\n"
            "+++ b/README.md\n"
            "+TODO/FIXME markers in docs\n"
            "diff --git a/tests/test_app.py b/tests/test_app.py\n"
            "+++ b/tests/test_app.py\n"
            "+api_key = 'supersecretvalue123'\n"
            "diff --git a/src/app.py b/src/app.py\n"
            "+++ b/src/app.py\n"
            "+pass\n"
        )
        filtered = claude_review.filter_diff_for_heuristics(diff)
        self.assertNotIn("README.md", filtered)
        self.assertNotIn("tests/test_app.py", filtered)
        self.assertIn("src/app.py", filtered)

    def test_analyze_pr_ignores_test_fixture_strings(self):
        diff = (
            "diff --git a/tests/test_app.py b/tests/test_app.py\n"
            "+++ b/tests/test_app.py\n"
            "+        diff = \"+++ b/app.py\\n+# TODO: handle edge case\\n\"\n"
            "+        diff = \"+++ b/app.py\\n+api_key = 'supersecretvalue123'\\n\"\n"
            "diff --git a/src/app.py b/src/app.py\n"
            "+++ b/src/app.py\n"
            "+def run():\n"
            "+    return 1\n"
        )
        metadata = {
            "title": "Add app",
            "body": "",
            "changed_files": [
                {"filename": "tests/test_app.py", "status": "modified", "additions": 2, "deletions": 0, "changes": 2},
                {"filename": "src/app.py", "status": "modified", "additions": 2, "deletions": 0, "changes": 2},
            ],
            "total_changes": 4,
            "commits": 1,
            "additions": 4,
            "deletions": 0,
            "labels": [],
        }
        review = claude_review.analyze_pr(metadata, diff)
        messages = [message for _, message in review["risks"]]
        self.assertFalse(any("TODO" in message for message in messages))
        self.assertFalse(any("hardcoded secrets" in message for message in messages))

    def test_analyze_pr_ignores_heuristic_definition_lines(self):
        diff = (
            "diff --git a/reviewer.py b/reviewer.py\n"
            "+++ b/reviewer.py\n"
            "+        todos = re.findall(\n"
            "+            r\"(?:\\+.*(?://|#|\\*).*?(?:TODO|FIXME|HACK|XXX).*)\",\n"
            "+            added_lines,\n"
            "+        )\n"
            "+        if todos:\n"
            "+            add_risk(\n"
            "+                \"low\",\n"
            "+                f\"{len(todos)} TODO/FIXME/HACK markers found in new code. \"\n"
            "+                \"Address them or track as follow-up issues.\",\n"
            "+            )\n"
        )
        metadata = {
            "title": "Add reviewer",
            "body": "",
            "changed_files": [
                {"filename": "reviewer.py", "status": "added", "additions": 8, "deletions": 0, "changes": 8},
            ],
            "total_changes": 8,
            "commits": 1,
            "additions": 8,
            "deletions": 0,
            "labels": [],
        }
        review = claude_review.analyze_pr(metadata, diff)
        messages = [message for _, message in review["risks"]]
        self.assertFalse(any("TODO" in message for message in messages))


class TokenResolutionTests(unittest.TestCase):
    def test_explicit_token_takes_priority(self):
        with unittest.mock.patch.dict("os.environ", {"GITHUB_TOKEN": "env-token"}, clear=False):
            self.assertEqual(
                claude_review.resolve_github_token("cli-token"),
                "cli-token",
            )

    def test_env_token_used_when_no_explicit(self):
        with unittest.mock.patch.dict("os.environ", {"GITHUB_TOKEN": "env-token"}, clear=False):
            with unittest.mock.patch("claude_review.subprocess.run") as run:
                self.assertEqual(claude_review.resolve_github_token(), "env-token")
                run.assert_not_called()

    def test_gh_auth_token_fallback(self):
        with unittest.mock.patch.dict("os.environ", {}, clear=True):
            with unittest.mock.patch(
                "claude_review.subprocess.run",
                return_value=unittest.mock.Mock(returncode=0, stdout="gh-token\n"),
            ) as run:
                self.assertEqual(claude_review.resolve_github_token(), "gh-token")
                run.assert_called_once()

    def test_returns_none_when_unavailable(self):
        with unittest.mock.patch.dict("os.environ", {}, clear=True):
            with unittest.mock.patch(
                "claude_review.subprocess.run",
                side_effect=FileNotFoundError,
            ):
                self.assertIsNone(claude_review.resolve_github_token())


class EdgeCaseTests(unittest.TestCase):
    def test_empty_diff_parses_no_files(self):
        self.assertEqual(claude_review.parse_diff_filenames(""), [])

    def test_whitespace_only_diff_parses_no_files(self):
        self.assertEqual(claude_review.parse_diff_filenames("   \n\n  "), [])

    def test_analyze_pr_with_empty_diff_and_no_files(self):
        metadata = {
            "title": "Empty PR",
            "body": "",
            "changed_files": [],
            "total_changes": 0,
            "commits": 0,
            "additions": 0,
            "deletions": 0,
            "labels": [],
        }
        review = claude_review.analyze_pr(metadata, diff="")
        self.assertIn("No file changes were detected", review["summary"])
        self.assertEqual(review["confidence"], "High")

    def test_filter_diff_by_filenames_empty_inputs(self):
        self.assertEqual(claude_review.filter_diff_by_filenames("", {"a.py"}), "")
        diff = "diff --git a/a.py b/a.py\n+++ b/a.py\n+pass\n"
        self.assertEqual(claude_review.filter_diff_by_filenames(diff, set()), "")

    def test_filter_diff_for_heuristics_empty_diff(self):
        self.assertEqual(claude_review.filter_diff_for_heuristics(""), "")

    def test_sanitize_pr_body_empty_and_whitespace(self):
        self.assertEqual(claude_review.sanitize_pr_body(""), "")
        self.assertEqual(claude_review.sanitize_pr_body("   \n\t  "), "")

    def test_metadata_from_diff_empty_produces_zero_totals(self):
        metadata = claude_review.metadata_from_diff("", title="No-op", author="bot")
        self.assertEqual(metadata["changed_files"], [])
        self.assertEqual(metadata["total_changes"], 0)


class CliErrorHandlingTests(unittest.TestCase):
    CLI = Path(__file__).resolve().parents[3] / "claude-review"

    def test_main_exits_when_no_token(self):
        with unittest.mock.patch(
            "sys.argv",
            ["claude-review", "--pr", "https://github.com/acme/widgets/pull/1"],
        ):
            with unittest.mock.patch("claude_review.resolve_github_token", return_value=None):
                with self.assertRaises(SystemExit) as ctx:
                    claude_review.main()
        self.assertEqual(ctx.exception.code, 1)

    def test_main_exits_on_invalid_pr_url(self):
        with unittest.mock.patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test"}, clear=False):
            result = subprocess.run(
                [str(self.CLI), "--pr", "not-a-valid-pr", "--token", "ghp_test"],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot parse PR", result.stderr)

    def test_main_exits_on_missing_diff_file(self):
        result = subprocess.run(
            [str(self.CLI), "--diff-file", "/tmp/does-not-exist-claude-review.diff"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error reading diff file", result.stderr)

    def test_main_reviews_empty_diff_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as handle:
            handle.write("")
            diff_path = handle.name
        try:
            result = subprocess.run(
                [
                    str(self.CLI),
                    "--diff-file",
                    diff_path,
                    "--title",
                    "Empty change set",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        finally:
            Path(diff_path).unlink(missing_ok=True)

        self.assertIn("No file changes were detected", result.stdout)
        self.assertIn("### Summary of Changes", result.stdout)

    def test_parse_args_requires_pr_or_diff_file(self):
        with unittest.mock.patch("sys.argv", ["claude-review"]):
            with self.assertRaises(SystemExit) as ctx:
                claude_review.parse_args()
        self.assertEqual(ctx.exception.code, 2)

    def test_parse_args_rejects_both_pr_and_diff_file(self):
        with unittest.mock.patch(
            "sys.argv",
            ["claude-review", "--pr", "1", "--diff-file", "changes.diff"],
        ):
            with self.assertRaises(SystemExit) as ctx:
                claude_review.parse_args()
        self.assertEqual(ctx.exception.code, 2)


class GithubApiErrorTests(unittest.TestCase):
    def test_fetch_pr_diff_returns_none_on_http_error(self):
        error = urllib.error.HTTPError(
            url="https://api.github.com/repos/a/b/pulls/1",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        with unittest.mock.patch(
            "claude_review.urllib.request.urlopen",
            side_effect=error,
        ):
            diff = claude_review.fetch_pr_diff("a", "b", 1, "ghp_test")

        self.assertIsNone(diff)

    def test_gh_auth_token_empty_stdout_returns_none(self):
        with unittest.mock.patch.dict("os.environ", {}, clear=True):
            with unittest.mock.patch(
                "claude_review.subprocess.run",
                return_value=unittest.mock.Mock(returncode=0, stdout="  \n"),
            ):
                self.assertIsNone(claude_review.resolve_github_token())

    def test_gh_auth_token_nonzero_exit_returns_none(self):
        with unittest.mock.patch.dict("os.environ", {}, clear=True):
            with unittest.mock.patch(
                "claude_review.subprocess.run",
                return_value=unittest.mock.Mock(returncode=1, stdout=""),
            ):
                self.assertIsNone(claude_review.resolve_github_token())


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
