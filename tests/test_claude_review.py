import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_review import (
    build_markdown_review,
    confidence_for,
    detect_risks,
    parse_diff,
    parse_pr_url,
)


SAMPLE_DIFF = """\
diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,4 +1,6 @@
 import subprocess
 
 def run_command(command):
-    return subprocess.run(command)
+    return subprocess.run(command, shell=True)
+
+PASSWORD = "dev"
diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Demo
+Updated setup notes.
"""


TESTED_DIFF = """\
diff --git a/src/math.py b/src/math.py
index 1111111..2222222 100644
--- a/src/math.py
+++ b/src/math.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
diff --git a/tests/test_math.py b/tests/test_math.py
index 3333333..4444444 100644
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -1,2 +1,5 @@
 from src.math import add
+
+def test_add():
+    assert add(1, 2) == 3
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = parse_pr_url("https://github.com/owner-name/repo.name/pull/123?tab=files")
        self.assertEqual(ref.owner, "owner-name")
        self.assertEqual(ref.repo, "repo.name")
        self.assertEqual(ref.number, 123)
        self.assertEqual(ref.diff_url, "https://github.com/owner-name/repo.name/pull/123.diff")

    def test_parse_diff_counts_files_and_lines(self):
        stats = parse_diff(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["src/app.py", "README.md"])
        self.assertEqual(stats.additions, 4)
        self.assertEqual(stats.deletions, 1)

    def test_detects_missing_tests_and_risky_patterns(self):
        stats = parse_diff(SAMPLE_DIFF)
        risks = detect_risks(stats)
        joined = "\n".join(risks)
        self.assertIn("Source code changed without matching test files", joined)
        self.assertIn("shell=True", joined)
        self.assertIn("secret-like variable", joined)

    def test_markdown_contains_required_sections(self):
        stats = parse_diff(SAMPLE_DIFF)
        markdown = build_markdown_review(stats)
        self.assertIn("### Summary of changes", markdown)
        self.assertIn("### Identified risks", markdown)
        self.assertIn("### Improvement suggestions", markdown)
        self.assertRegex(markdown, r"### Confidence score: (Low|Medium|High)")

    def test_high_confidence_for_small_tested_change(self):
        stats = parse_diff(TESTED_DIFF)
        risks = detect_risks(stats)
        self.assertEqual(confidence_for(stats, risks), "High")

    def test_low_confidence_when_truncated(self):
        stats = parse_diff(TESTED_DIFF, max_chars=20)
        risks = detect_risks(stats)
        self.assertEqual(confidence_for(stats, risks), "Low")


if __name__ == "__main__":
    unittest.main()
