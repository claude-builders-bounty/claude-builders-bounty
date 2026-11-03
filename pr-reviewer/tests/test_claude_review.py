import contextlib
import importlib.machinery
import importlib.util
import io
import os
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "mock_review.md")

_loader = importlib.machinery.SourceFileLoader("claude_review", os.path.join(ROOT, "claude-review"))
_spec = importlib.util.spec_from_loader("claude_review", _loader)
cr = importlib.util.module_from_spec(_spec)
_loader.exec_module(cr)

URL = "https://github.com/o/r/pull/7"
GOOD = open(FIXTURE, encoding="utf-8").read()


class Tests(unittest.TestCase):
    def test_parse_url(self):
        self.assertEqual(cr.parse_pr_url(URL), ("o", "r", 7))
        self.assertEqual(cr.parse_pr_url(URL + "/"), ("o", "r", 7))

    def test_parse_url_invalid(self):
        for bad in ["https://github.com/o/r/issues/7", "nonsense", "https://evil.com/o/r/pull/1"]:
            with self.assertRaises(cr.ReviewError) as c:
                cr.parse_pr_url(bad)
            self.assertEqual(c.exception.code, 2)

    def test_truncate_at_file_boundary(self):
        d = "diff --git a/a b/a\n" + "x\n" * 10 + "diff --git a/b b/b\n" + "y\n" * 10
        out = cr.truncate_diff(d, 40)
        self.assertTrue(out.endswith("[diff truncated]\n"))
        self.assertNotIn("diff --git a/b", out)
        self.assertEqual(cr.truncate_diff("short", 40), "short")

    def test_prompt(self):
        p = cr.build_prompt({"title": "T", "body": "B"}, "diff --git a/a b/a\n+hi")
        self.assertIn("+hi", p)
        self.assertIn("untrusted", p)
        for s in cr.SECTIONS:
            self.assertIn("## " + s, p)

    def test_format_good(self):
        out = cr.format_review(GOOD, URL)
        self.assertIn("Claude PR Review", out)
        self.assertIn("## Confidence", out)

    def test_format_malformed(self):
        with self.assertRaises(cr.ReviewError):
            cr.format_review("## Summary\nonly this", URL)
        with self.assertRaises(cr.ReviewError):
            cr.format_review(GOOD.replace("Medium", "Unsure"), URL)

    def test_no_key_clean_exit(self):
        env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "CLAUDE_REVIEW_MOCK")}
        err = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(cr.shutil, "which", return_value=None), \
                mock.patch.object(cr, "fetch_pr", return_value=({"title": "t", "body": ""}, "d")), \
                contextlib.redirect_stderr(err):
            self.assertEqual(cr.main(["--pr", URL]), 1)
        self.assertIn("ANTHROPIC_API_KEY", err.getvalue())

    def test_end_to_end_mock(self):
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"CLAUDE_REVIEW_MOCK": FIXTURE}), \
                mock.patch.object(cr, "fetch_pr", return_value=({"title": "t", "body": ""}, "d")), \
                contextlib.redirect_stdout(out):
            self.assertEqual(cr.main(["--pr", URL]), 0)
        self.assertIn("## Risks", out.getvalue())

    def test_post_requires_token(self):
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(cr.ReviewError):
                cr.post_comment("o", "r", 7, "x")


if __name__ == "__main__":
    unittest.main()
