import unittest

from claude_review_agent.reviewer import analyze, render_markdown


class ReviewerTests(unittest.TestCase):
    def test_review_includes_required_sections(self) -> None:
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
+import subprocess
+API_TOKEN = "example"
 print("hello")
"""
        review = analyze("https://github.com/example/project/pull/1", diff, {"title": "Add runner"})
        markdown = render_markdown(review)

        self.assertIn("Summary of changes", markdown)
        self.assertIn("Identified risks", markdown)
        self.assertIn("Improvement suggestions", markdown)
        self.assertIn("Confidence score:", markdown)
        self.assertIn("Command execution", markdown)
        self.assertIn("Credential-like", markdown)

    def test_docs_only_change_has_low_risk_signal(self) -> None:
        diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Project
+Adds usage notes.
"""
        review = analyze("https://github.com/example/project/pull/2", diff, {"title": "Update docs"})

        self.assertEqual(review.confidence, "High")
        self.assertTrue(any("Documentation-only" in finding.message for finding in review.risks))


if __name__ == "__main__":
    unittest.main()
