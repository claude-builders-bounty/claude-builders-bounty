import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from claude_review.cli import _post_comment, main
from claude_review.github import PullRequest
from claude_review.review import Review, ReviewError, render_markdown


class PostingGuardTests(unittest.TestCase):
    def test_post_refuses_non_interactive_runs(self):
        with patch("claude_review.cli.sys.stdin", io.StringIO("")) as stdin:
            with patch.object(stdin, "isatty", return_value=False):
                with patch("claude_review.cli.subprocess.run") as run:
                    with self.assertRaisesRegex(ReviewError, "interactive terminal"):
                        _post_comment(PullRequest("example", "repo", 3), "review")
        run.assert_not_called()

    def test_json_mode_shows_exact_markdown_before_post_confirmation(self):
        review = Review(
            summary=("Adds a safe review CLI.", "The output is schema checked."),
            risks=(),
            suggestions=("Add an integration test.",),
            confidence="Medium",
        )
        pull_request = PullRequest("example", "repo", 4)
        url = pull_request.canonical_url
        output = io.StringIO()
        errors = io.StringIO()
        with (
            patch("claude_review.cli.fetch_pull_request_diff", return_value="diff"),
            patch("claude_review.cli.run_claude_review", return_value=review),
            patch("claude_review.cli._post_comment", return_value=False) as post,
            redirect_stdout(output),
            redirect_stderr(errors),
        ):
            self.assertEqual(main(["--pr", url, "--format", "json", "--post"]), 0)

        stdout = output.getvalue()
        output_json = json.loads(stdout.split("\n\nComment to post:", 1)[0])
        self.assertEqual(output_json["review"], review.as_dict())
        self.assertIn("Comment to post:", stdout)
        self.assertIn(render_markdown(url, review), stdout)
        self.assertIn("Not posted.", errors.getvalue())
        post.assert_called_once_with(pull_request, render_markdown(url, review))


if __name__ == "__main__":
    unittest.main()
