import unittest
from pathlib import Path
from unittest.mock import patch

from claude_review import (
    PullRequestURL,
    analyze_diff,
    fetch_pr_diff,
    format_review,
    parse_pr_url,
)


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,5 +1,10 @@
 import os
+import subprocess
+
+SECRET_KEY = "dev-secret"
 
 def hello(name):
+    subprocess.run("rm -rf /tmp/demo", shell=True)
     return f"hello {name}"
+
+def unused():
+    return SECRET_KEY
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url_extracts_owner_repo_and_number(self):
        pr = parse_pr_url("https://github.com/octocat/hello-world/pull/42")
        self.assertEqual(pr, PullRequestURL("octocat", "hello-world", 42))

    def test_parse_pr_url_rejects_non_pr_urls(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/octocat/hello-world/issues/42")

    def test_analyze_diff_summarizes_files_and_changed_lines(self):
        analysis = analyze_diff(SAMPLE_DIFF)
        self.assertEqual(analysis.files_changed, ["app.py"])
        self.assertEqual(analysis.added_lines, 5)
        self.assertEqual(analysis.removed_lines, 0)
        self.assertIn("app.py", analysis.summary)

    def test_analyze_diff_identifies_risks_and_suggestions(self):
        analysis = analyze_diff(SAMPLE_DIFF)
        risks = "\n".join(analysis.risks)
        suggestions = "\n".join(analysis.suggestions)
        self.assertIn("shell=True", risks)
        self.assertIn("secret", risks.lower())
        self.assertIn("tests", suggestions.lower())
        self.assertEqual(analysis.confidence, "High")

    def test_format_review_contains_required_markdown_sections(self):
        review = format_review(analyze_diff(SAMPLE_DIFF), "https://github.com/octocat/hello-world/pull/42")
        self.assertIn("## Summary of changes", review)
        self.assertIn("## Identified risks", review)
        self.assertIn("## Improvement suggestions", review)
        self.assertIn("## Confidence score", review)
        self.assertIn("High", review)

    def test_fetch_pr_diff_uses_github_diff_endpoint(self):
        with patch("claude_review.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b"diff --git a/a b/a\n"
            diff = fetch_pr_diff(PullRequestURL("octocat", "hello-world", 42))
        self.assertIn("diff --git", diff)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://patch-diff.githubusercontent.com/raw/octocat/hello-world/pull/42.diff")


if __name__ == "__main__":
    unittest.main()
