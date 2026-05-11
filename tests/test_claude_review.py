import json
import unittest

from tools.claude_review import offline_review, parse_pr_url, summarize_diff


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,6 @@
+import subprocess
+
 def run(name):
-    return "hello " + name
+    return subprocess.check_output(["echo", name], text=True)
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_run():
+    assert True
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_parse_pr_url(self):
        parsed = parse_pr_url("https://github.com/example/repo/pull/123")
        self.assertEqual(parsed.owner, "example")
        self.assertEqual(parsed.repo, "repo")
        self.assertEqual(parsed.number, "123")
        self.assertEqual(parsed.diff_url, "https://github.com/example/repo/pull/123.diff")

    def test_summarize_diff(self):
        summary = summarize_diff(SAMPLE_DIFF)
        self.assertEqual(summary.files, ["app.py", "tests/test_app.py"])
        self.assertTrue(summary.tests_changed)
        self.assertGreaterEqual(summary.additions, 5)
        self.assertIn("Command execution or dynamic evaluation touched.", summary.risk_flags)

    def test_offline_review_has_required_sections(self):
        summary = summarize_diff(SAMPLE_DIFF)
        review = offline_review("https://github.com/example/repo/pull/123", summary)
        self.assertIn("## Summary", review)
        self.assertIn("## Identified risks", review)
        self.assertIn("## Improvement suggestions", review)
        self.assertIn("## Confidence", review)

    def test_json_serializable_summary(self):
        summary = summarize_diff(SAMPLE_DIFF)
        payload = json.loads(json.dumps(summary.__dict__))
        self.assertIn("files", payload)
        self.assertIn("risk_flags", payload)


if __name__ == "__main__":
    unittest.main()

