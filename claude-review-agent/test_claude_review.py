#!/usr/bin/env python3
"""claude-review-agent 的核心逻辑测试。"""

from __future__ import annotations

import unittest

from claude_review import PullRequestMetadata, PullRequestRef, analyze, parse_diff, parse_pr_url, render_markdown


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 import os
+import subprocess
+subprocess.run(user_input, shell=True)
 print("hello")
diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Demo
+More docs.
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        parsed = parse_pr_url("https://github.com/example/project/pull/123")
        self.assertEqual(parsed.owner, "example")
        self.assertEqual(parsed.repo, "project")
        self.assertEqual(parsed.number, 123)

    def test_parse_diff_collects_files_and_lines(self) -> None:
        files = parse_diff(SAMPLE_DIFF)
        self.assertEqual([file.path for file in files], ["app.py", "README.md"])
        self.assertEqual(files[0].additions, 2)
        self.assertEqual(files[1].additions, 1)

    def test_analyze_flags_missing_tests_and_dangerous_patterns(self) -> None:
        pr = PullRequestRef("example", "project", 123, "https://github.com/example/project/pull/123")
        metadata = PullRequestMetadata(
            title="Add subprocess call",
            author="alice",
            base="main",
            head="feature",
            additions=3,
            deletions=0,
            changed_files=2,
        )
        result = analyze(pr, metadata, parse_diff(SAMPLE_DIFF))
        joined_risks = "\n".join(result.risks)
        self.assertIn("No test files", joined_risks)
        self.assertIn("dangerous", joined_risks)
        self.assertEqual(result.confidence, "Medium")

    def test_render_markdown_contains_required_sections(self) -> None:
        pr = PullRequestRef("example", "project", 123, "https://github.com/example/project/pull/123")
        metadata = PullRequestMetadata(
            title="Docs update",
            author="alice",
            base="main",
            head="docs",
            additions=1,
            deletions=0,
            changed_files=1,
        )
        result = analyze(pr, metadata, parse_diff(SAMPLE_DIFF))
        markdown = render_markdown(pr, metadata, result)
        self.assertIn("## Summary", markdown)
        self.assertIn("## Identified Risks", markdown)
        self.assertIn("## Improvement Suggestions", markdown)
        self.assertIn("## Confidence Score", markdown)


if __name__ == "__main__":
    unittest.main()
