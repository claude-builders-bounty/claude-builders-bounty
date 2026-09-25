"""Unit tests for claude_review.py — run with: python -m unittest discover tests -v"""
import os
import sys
import unittest
from argparse import Namespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import claude_review as cr


def ns(**kw):
    return Namespace(pr=kw.get("pr"), repo=kw.get("repo"),
                     number=kw.get("number"), diff_file=None, write=None)


class TestParsePr(unittest.TestCase):
    def test_full_url(self):
        self.assertEqual(cr.parse_pr(ns(pr="https://github.com/pallets/click/pull/3782")),
                         ("pallets/click", "3782"))

    def test_url_with_extra_path_and_query(self):
        url = "https://github.com/owner/repo-name.x/pull/12/files#diff-1"
        self.assertEqual(cr.parse_pr(ns(pr=url)), ("owner/repo-name.x", "12"))

    def test_repo_number_pair(self):
        self.assertEqual(cr.parse_pr(ns(repo="pallets/click", number="42")),
                         ("pallets/click", "42"))

    def test_repo_without_number_raises(self):
        with self.assertRaises(cr.ReviewError):
            cr.parse_pr(ns(repo="pallets/click"))

    def test_bad_repo_shape_raises(self):
        with self.assertRaises(cr.ReviewError):
            cr.parse_pr(ns(repo="not-a-repo-ref", number="1"))

    def test_nothing_provided_raises(self):
        with self.assertRaises(cr.ReviewError):
            cr.parse_pr(ns())


class TestTruncateMiddle(unittest.TestCase):
    def test_short_text_untouched(self):
        self.assertEqual(cr.truncate_middle("abc"), "abc")

    def test_long_text_truncated_with_notice(self):
        text = "x" * 10000
        out = cr.truncate_middle(text, limit=100)
        self.assertIn("[... truncated by claude-review", out)
        self.assertLess(len(out), 200)

    def test_truncation_preserves_head_and_tail(self):
        text = "HEAD" + "m" * 10000 + "TAIL"
        out = cr.truncate_middle(text, limit=400)
        self.assertTrue(out.startswith("HEAD"))
        self.assertTrue(out.rstrip().endswith("TAIL"))


class TestRunGh(unittest.TestCase):
    def test_missing_gh_binary_raises_clean_error(self):
        with mock.patch.object(cr, "GH", "definitely-not-a-real-binary-xyz"):
            with self.assertRaises(cr.ReviewError) as ctx:
                cr._run_gh(["--version"])
            self.assertIn("gh CLI not found", str(ctx.exception))


class TestCallLlmKeyGate(unittest.TestCase):
    def test_missing_key_raises_before_network(self):
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(cr.ReviewError) as ctx:
                cr.call_llm("ctx", "diff")
            self.assertIn("ANTHROPIC_API_KEY", str(ctx.exception))


class TestValidateReview(unittest.TestCase):
    VALID = ("## Summary\nA bounded change.\n\n## Risks\n- None identified.\n\n"
             "## Suggestions\n- None.\n\n## Confidence\nHigh — tests cover the change.")

    def test_valid_review(self):
        self.assertEqual(cr.validate_review(self.VALID), self.VALID)

    def test_missing_section_rejected(self):
        with self.assertRaises(cr.ReviewError):
            cr.validate_review("## Summary\nA change.\n")

    def test_unsafe_markup_rejected(self):
        with self.assertRaises(cr.ReviewError):
            cr.validate_review(self.VALID + "\n<script>alert(1)</script>")

    def test_environment_delimiter_rejected(self):
        with self.assertRaises(cr.ReviewError):
            cr.validate_review(self.VALID + "\nCLAUDE_REVIEW_EOF")

    def test_length_limit_rejected(self):
        with self.assertRaises(cr.ReviewError):
            cr.validate_review(self.VALID + "x" * cr.MAX_REVIEW_CHARS)


if __name__ == "__main__":
    unittest.main()
