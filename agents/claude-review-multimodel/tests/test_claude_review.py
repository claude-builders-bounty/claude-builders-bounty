"""Tests for claude_review.py — heuristic backend + CLI parsing."""

import json
import os
import sys
import textwrap
import unittest
from unittest.mock import patch

# Add module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from claude_review import (
    PRMetadata,
    Risk,
    Review,
    format_review,
    heuristic_review,
    parse_pr_ref,
    truncate_diff,
    parse_diff_stats,
)


class TestParsePRRef(unittest.TestCase):
    def test_full_url(self):
        self.assertEqual(parse_pr_ref("https://github.com/owner/repo/pull/123"), ("owner", "repo", 123))

    def test_short_ref(self):
        self.assertEqual(parse_pr_ref("owner/repo#456"), ("owner", "repo", 456))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_ref("not-a-valid-ref")


class TestTruncateDiff(unittest.TestCase):
    def test_no_truncation(self):
        self.assertEqual(truncate_diff("hello", 1000), "hello")

    def test_truncation(self):
        long_diff = "x" * 1000
        result = truncate_diff(long_diff, 100)
        self.assertIn("DIFF TRUNCATED", result)
        self.assertLessEqual(len(result.encode("utf-8")), 200)


class TestParseDiffStats(unittest.TestCase):
    def test_basic_diff(self):
        diff = textwrap.dedent("""\
            diff --git a/foo.py b/foo.py
            --- a/foo.py
            +++ b/foo.py
            @@ -1,3 +1,4 @@
             line1
            +added_line
             line2
            -removed_line
            """)
        stats = parse_diff_stats(diff)
        self.assertIn("foo.py", stats)
        self.assertEqual(stats["foo.py"]["additions"], 1)
        self.assertEqual(stats["foo.py"]["deletions"], 1)


class TestHeuristicReview(unittest.TestCase):
    def test_clean_diff(self):
        diff = textwrap.dedent("""\
            diff --git a/clean.py b/clean.py
            --- a/clean.py
            +++ b/clean.py
            @@ -1,2 +1,3 @@
             line1
            +x = 1
             line2
            """)
        review = heuristic_review(diff)
        self.assertEqual(review.backend, "heuristic")
        self.assertEqual(review.confidence_score, "Low")
        self.assertEqual(len(review.risks), 0)

    def test_secret_detection(self):
        diff = textwrap.dedent("""\
            diff --git a/config.py b/config.py
            --- a/config.py
            +++ b/config.py
            @@ -0,0 +1 @@
            +API_KEY = "sk-ant-api03-aaaaaaaaaaaaaaaaaaaaaaaaaaa"
            """)
        review = heuristic_review(diff)
        critical = [r for r in review.risks if r.severity == "critical"]
        self.assertTrue(len(critical) > 0, "Should detect hardcoded secret")
        self.assertEqual(critical[0].category, "security")

    def test_debug_statement(self):
        diff = textwrap.dedent("""\
            diff --git a/app.py b/app.py
            --- a/app.py
            +++ b/app.py
            @@ -1,2 +1,3 @@
             def run():
            +    print("debugging value", x)
                 return x
            """)
        review = heuristic_review(diff)
        debug_risks = [r for r in review.risks if r.category == "quality" and "debug" in r.description.lower()]
        self.assertTrue(len(debug_risks) > 0, "Should detect debug print statement")

    def test_empty_catch(self):
        diff = textwrap.dedent("""\
            diff --git a/handler.py b/handler.py
            --- a/handler.py
            +++ b/handler.py
            @@ -1,3 +1,5 @@
             try:
            +    do_thing()
            +except:
            +    pass
            """)
        review = heuristic_review(diff)
        bug_risks = [r for r in review.risks if r.severity == "high"]
        self.assertTrue(len(bug_risks) > 0, "Should detect bare except:pass")

    def test_todo_comment(self):
        diff = textwrap.dedent("""\
            diff --git a/main.py b/main.py
            --- a/main.py
            +++ b/main.py
            @@ -1 +1,2 @@
            +# TODO: refactor this later
            +x = compute()
            """)
        review = heuristic_review(diff)
        todo_risks = [r for r in review.risks if "TODO" in r.description]
        self.assertTrue(len(todo_risks) > 0, "Should detect TODO comment")


class TestFormatReview(unittest.TestCase):
    def test_basic_format(self):
        review = Review(
            summary="Test summary.",
            risks=[Risk("high", "bug", "Something bad", "file.py")],
            suggestions=["**bug** Fix the thing"],
            confidence_score="Medium",
            confidence_rationale="Found patterns",
            backend="heuristic",
            model="heuristic",
        )
        meta = PRMetadata(title="Test PR", author="testuser", files_changed=1, additions=10, deletions=5)
        output = format_review(review, meta)
        self.assertIn("## Summary", output)
        self.assertIn("## Identified Risks", output)
        self.assertIn("## Improvement Suggestions", output)
        self.assertIn("## Confidence", output)
        self.assertIn("| 1 | high | bug | Something bad | file.py |", output)


if __name__ == "__main__":
    unittest.main()