import unittest

from claude_review import PullRequestRef, build_offline_review, parse_pr_url


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,7 @@
+import os
+
 def handler(request):
-    return {"ok": True}
+    token = os.environ.get("TOKEN")
+    if request.get("force"):
+        return {"token": token}
+    return {"ok": True}
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_handler():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        parsed = parse_pr_url("https://github.com/acme/widgets/pull/123")

        self.assertEqual(
            parsed,
            PullRequestRef(owner="acme", repo="widgets", number=123),
        )

    def test_offline_review_contains_required_sections(self):
        review = build_offline_review(
            pr_url="https://github.com/acme/widgets/pull/123",
            title="Expose token in handler",
            changed_files=["app.py", "tests/test_app.py"],
            diff=SAMPLE_DIFF,
        )

        self.assertIn("## Summary", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertIn("## Confidence", review)
        self.assertRegex(review, r"Confidence: (Low|Medium|High)")
        self.assertIn("app.py", review)


if __name__ == "__main__":
    unittest.main()
