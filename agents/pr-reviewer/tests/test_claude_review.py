#!/usr/bin/env python3
"""Tests for claude_review.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import claude_review as cr_mod

parse_diff = cr_mod.parse_diff
analyze_files = cr_mod.analyze_files
format_review = cr_mod.format_review
parse_pr_url = cr_mod.parse_pr_url


class TestParsePRUrl(unittest.TestCase):
    def test_standard_url(self):
        owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(num, "123")

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://example.com/not-a-pr")


class TestParseDiff(unittest.TestCase):
    def test_single_file_addition(self):
        diff = """diff --git a/main.py b/main.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/main.py
@@ -0,0 +1,3 @@
+def hello():
+    print("hello world")
+    return 42
"""
        files = parse_diff(diff)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["file_b"], "main.py")
        self.assertEqual(files[0]["status"], "added")
        self.assertEqual(files[0]["additions"], 3)
        self.assertEqual(files[0]["deletions"], 0)

    def test_multiple_files(self):
        diff = """diff --git a/a.txt b/a.txt
--- a/a.txt
+++ b/a.txt
@@ -1 +1,2 @@
 old
+new
diff --git a/b.txt b/b.txt
--- a/b.txt
+++ b/b.txt
@@ -1 +1 @@
-old
+new
"""
        files = parse_diff(diff)
        self.assertEqual(len(files), 2)

    def test_deletion(self):
        diff = """diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-old line 1
-old line 2
"""
        files = parse_diff(diff)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["status"], "deleted")
        self.assertEqual(files[0]["deletions"], 2)


class TestAnalyzeFiles(unittest.TestCase):
    def test_clean_diff(self):
        diff = """diff --git a/hello.py b/hello.py
--- a/hello.py
+++ b/hello.py
@@ -1 +1,2 @@
-old line
+new line
+another new line
"""
        files = parse_diff(diff)
        result = analyze_files(files)
        self.assertEqual(result["total_files"], 1)
        self.assertEqual(result["total_additions"], 2)
        self.assertEqual(result["total_deletions"], 1)
        self.assertEqual(result["confidence"], "High")

    def test_detects_todo(self):
        diff = """diff --git a/source.py b/source.py
--- a/source.py
+++ b/source.py
@@ -1 +1,2 @@
+# TODO: refactor this
+def func():
"""
        files = parse_diff(diff)
        result = analyze_files(files)
        has_todo = any("TODO" in imp for imp in result["improvements"])
        self.assertTrue(has_todo)

    def test_detects_debug_print(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,3 @@
+import pdb; pdb.set_trace()
+def func():
+    print("debug")
"""
        files = parse_diff(diff)
        result = analyze_files(files)
        # Should flag the debug statement
        has_debug = any("print" in r or "pdb" in r for r in result["risks"])
        self.assertTrue(has_debug)


class TestFormatReview(unittest.TestCase):
    def test_output_structure(self):
        review = {
            "summary": "Test summary.",
            "total_files": 1,
            "total_additions": 10,
            "total_deletions": 5,
            "risks": ["Risk 1"],
            "improvements": ["Suggestion 1"],
            "findings": [],
            "confidence": "Medium",
        }
        output = format_review(review, "https://github.com/test/repo/pull/1", "Test PR")
        self.assertIn("Test PR", output)
        self.assertIn("Risk 1", output)
        self.assertIn("Suggestion 1", output)
        self.assertIn("Medium", output)


if __name__ == "__main__":
    unittest.main()
