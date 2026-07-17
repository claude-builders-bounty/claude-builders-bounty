#!/usr/bin/env python3
"""Tests drive the real claude_review module (parse + analyze_diff + CLI)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import claude_review as cr

DIR = Path(__file__).resolve().parent


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_ref(self):
        o, r, n = cr.parse_pr_ref("https://github.com/a/b/pull/42")
        self.assertEqual((o, r, n), ("a", "b", 42))
        o, r, n = cr.parse_pr_ref("a/b#7")
        self.assertEqual((o, r, n), ("a", "b", 7))

    def test_analyze_blocks_rm_rf_in_diff(self):
        diff = """diff --git a/x.sh b/x.sh
+++ b/x.sh
+rm -rf /tmp/foo
"""
        rev = cr.analyze_diff(diff, title="cleanup")
        self.assertTrue(any("rm -rf" in x.lower() for x in rev.risks))
        md = rev.to_markdown()
        self.assertIn("## Summary", md)
        self.assertIn("## Identified risks", md)
        self.assertIn("## Improvement suggestions", md)
        self.assertIn("Confidence", md)

    def test_allows_clean_small_diff(self):
        diff = """diff --git a/hi.txt b/hi.txt
+++ b/hi.txt
+hello
"""
        rev = cr.analyze_diff(diff, title="docs")
        self.assertIn(rev.confidence, ("Low", "Medium", "High"))
        self.assertIn("file", rev.summary.lower())

    def test_cli_diff_file(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "p.diff"
            d.write_text(
                "diff --git a/a b/a\n+++ b/a\n+ok\n", encoding="utf-8"
            )
            out = Path(td) / "out.md"
            r = subprocess.run(
                [
                    sys.executable,
                    str(DIR / "claude_review.py"),
                    "--diff",
                    str(d),
                    "-o",
                    str(out),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            text = out.read_text(encoding="utf-8")
            self.assertIn("# PR Review", text)
            self.assertIn("Summary", text)


if __name__ == "__main__":
    unittest.main()
