import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).parents[1] / "claude_review.py"
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
cr = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = cr
SPEC.loader.exec_module(cr)

GOOD_REVIEW = """## Summary
This changes a small parser. It adds validation.

## Risks
- A malformed input could still be rejected late.

## Improvement suggestions
- Add a boundary test.

## Confidence
High"""

class ClaudeReviewTests(unittest.TestCase):
    def test_validate_pr_url(self):
        url = "https://github.com/openai/openai-python/pull/123"
        self.assertEqual(cr.validate_pr_url(url + "/"), url)
        with self.assertRaises(Exception):
            cr.validate_pr_url("https://example.com/x/y/pull/1")

    def test_clip_diff_marks_truncation(self):
        clipped, truncated = cr.clip_diff("abcdef", 3)
        self.assertTrue(truncated)
        self.assertIn("DIFF TRUNCATED", clipped)

    def test_build_prompt_contains_required_contract(self):
        meta = {
            "url": "https://github.com/o/r/pull/1",
            "title": "Fix thing",
            "baseRefName": "main",
            "headRefName": "fix",
            "author": {"login": "dev"},
            "additions": 2,
            "deletions": 1,
            "files": [{"path": "app.py"}],
        }
        prompt = cr.build_prompt(meta, "diff --git a/app.py b/app.py", False)
        for heading in cr.REQUIRED_HEADINGS:
            self.assertIn(heading, prompt)
        self.assertIn("Do not invent", prompt)
        self.assertIn("app.py", prompt)

    def test_validate_review_rejects_bad_confidence(self):
        cr.validate_review(GOOD_REVIEW)
        with self.assertRaises(cr.ReviewError):
            cr.validate_review(GOOD_REVIEW.replace("High", "Very High"))

    @mock.patch.object(cr, "invoke_claude", return_value=GOOD_REVIEW)
    @mock.patch.object(cr, "fetch_pr")
    def test_main_prints_review(self, fetch_pr, invoke_claude):
        fetch_pr.return_value = (
            {
                "url": "https://github.com/o/r/pull/1",
                "title": "Fix",
                "files": [],
                "author": {"login": "dev"},
            },
            "diff",
        )
        out = io.StringIO()
        with redirect_stdout(out):
            code = cr.main(["--pr", "https://github.com/o/r/pull/1"])
        self.assertEqual(code, 0)
        self.assertIn("## Confidence", out.getvalue())
        invoke_claude.assert_called_once()
    @mock.patch.object(cr, "post_review")
    @mock.patch.object(cr, "invoke_claude", return_value=GOOD_REVIEW)
    @mock.patch.object(cr, "fetch_pr", return_value=({"files": []}, "diff"))
    def test_post_flag_posts_exact_review(self, _fetch, _invoke, post_review):
        cr.main(["--pr", "https://github.com/o/r/pull/2", "--post"])
        post_review.assert_called_once_with(
            "https://github.com/o/r/pull/2", GOOD_REVIEW
        )

if __name__ == "__main__":
    unittest.main()
