import unittest

from pr_review_agent_import import load_module


claude_review = load_module()


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
 def run(name):
+    token = "example-token-placeholder"
+    eval(name)
     return name
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_run():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/openai/example/pull/123"),
            ("openai", "example", "123"),
        )

    def test_parse_diff_counts_files_and_lines(self):
        files = claude_review.parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual([file.path for file in files], ["app.py", "tests/test_app.py"])
        self.assertEqual(sum(file.additions for file in files), 4)
        self.assertEqual(sum(file.deletions for file in files), 0)

    def test_review_contains_required_sections(self):
        facts = claude_review.ReviewFacts(
            owner="openai",
            repo="example",
            number="123",
            title="Example change",
            files=claude_review.parse_unified_diff(SAMPLE_DIFF),
        )
        markdown = claude_review.render_review(facts)
        self.assertIn("### Summary of Changes", markdown)
        self.assertIn("### Identified Risks", markdown)
        self.assertIn("### Improvement Suggestions", markdown)
        self.assertIn("### Confidence Score", markdown)
        self.assertIn("credential-like", markdown)
        self.assertIn("evaluate dynamic input", markdown)


if __name__ == "__main__":
    unittest.main()
