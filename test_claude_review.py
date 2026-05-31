import unittest
import contextlib
import io
from unittest.mock import patch

import claude_review


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 print("hello")
+API_KEY = "not-a-real-test-token"
+eval(user_input)
"""

DELETION_DIFF = """diff --git a/old.py b/old.py
deleted file mode 100644
index 1111111..0000000
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-print("obsolete")
-print("remove me")
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/example/project/pull/42"),
            ("example", "project", "42"),
        )

    def test_parse_pr_shorthand(self):
        self.assertEqual(claude_review.parse_pr_url("example/project/42"), ("example", "project", "42"))
        self.assertEqual(claude_review.parse_pr_url("example/project#42"), ("example", "project", "42"))

    def test_summarize_diff_counts_files_and_additions(self):
        stats = claude_review.summarize_diff(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["app.py"])
        self.assertEqual(stats.additions, 2)
        self.assertEqual(stats.deletions, 0)
        self.assertEqual(stats.hunks, 1)

    def test_summarize_diff_tracks_deleted_files(self):
        stats = claude_review.summarize_diff(DELETION_DIFF)
        self.assertEqual(stats.files, ["old.py"])
        self.assertEqual(stats.additions, 0)
        self.assertEqual(stats.deletions, 2)
        self.assertEqual(stats.hunks, 1)

    def test_risk_detection_finds_security_patterns(self):
        stats = claude_review.summarize_diff(SAMPLE_DIFF)
        risks = {risk.title for risk in claude_review.find_risks(stats)}
        self.assertIn("Possible secret added", risks)
        self.assertIn("Dynamic code execution", risks)

    def test_render_review_has_required_sections(self):
        stats = claude_review.summarize_diff(SAMPLE_DIFF)
        output = claude_review.render_review("https://github.com/example/project/pull/42", stats)
        self.assertIn("## Summary", output)
        self.assertIn("## Identified Risks", output)
        self.assertIn("## Improvement Suggestions", output)
        self.assertIn("## Confidence:", output)

    def test_classify_files_detects_python_test_naming(self):
        groups = claude_review.classify_files(["test_claude_review.py", "tests/unit/test_api.py"])
        self.assertEqual(groups, ["tests"])

    def test_post_review_creates_comment_with_marker(self):
        calls: list[list[str]] = []

        def fake_run_gh_api(args, timeout):
            calls.append(args)
            if args == ["repos/example/project/issues/42/comments", "--paginate"]:
                return "[]"
            return '{"html_url":"https://github.com/example/project/pull/42#issuecomment-1"}'

        with patch.object(claude_review, "run_gh_api", side_effect=fake_run_gh_api):
            url = claude_review.post_review("https://github.com/example/project/pull/42", "## Summary", 30)

        self.assertEqual(url, "https://github.com/example/project/pull/42#issuecomment-1")
        self.assertEqual(calls[1][0:3], ["--method", "POST", "repos/example/project/issues/42/comments"])
        self.assertIn(claude_review.COMMENT_MARKER, calls[1][-1])

    def test_post_review_updates_existing_marker_comment(self):
        calls: list[list[str]] = []

        def fake_run_gh_api(args, timeout):
            calls.append(args)
            if args == ["repos/example/project/issues/42/comments", "--paginate"]:
                return '[{"id":123,"body":"<!-- claude-review:bot -->\\nold"}]'
            return '{"html_url":"https://github.com/example/project/pull/42#issuecomment-123"}'

        with patch.object(claude_review, "run_gh_api", side_effect=fake_run_gh_api):
            url = claude_review.post_review("https://github.com/example/project/pull/42", "## Summary", 30)

        self.assertEqual(url, "https://github.com/example/project/pull/42#issuecomment-123")
        self.assertEqual(calls[1][0:3], ["--method", "PATCH", "repos/example/project/issues/comments/123"])

    def test_main_writes_output_file(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.object(claude_review, "read_diff", return_value=SAMPLE_DIFF),
            patch.object(claude_review.Path, "write_text") as write_text,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = claude_review.main(["--diff-file", "sample.diff", "--output", "review.md"])

        self.assertEqual(exit_code, 0)
        written_body = write_text.call_args.args[0]
        self.assertIn("## Summary", written_body)
        self.assertEqual(write_text.call_args.kwargs, {"encoding": "utf-8"})

    def test_post_requires_pr_url(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = claude_review.main(["--diff-file", "sample.diff", "--post"])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
