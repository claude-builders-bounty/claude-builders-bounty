import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "agents" / "pr-review-agent" / "claude_review.py"
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = claude_review
SPEC.loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/app/auth/login.py b/app/auth/login.py
index 1111111..2222222 100644
--- a/app/auth/login.py
+++ b/app/auth/login.py
@@ -1,3 +1,7 @@
 def login(user):
-    return user
+    if not user:
+        raise ValueError("user is required")
+    return {"id": user.id}
diff --git a/tests/test_login.py b/tests/test_login.py
index 3333333..4444444 100644
--- a/tests/test_login.py
+++ b/tests/test_login.py
@@ -0,0 +1,4 @@
+def test_login_requires_user():
+    with pytest.raises(ValueError):
+        login(None)
"""


class PrReviewAgentTests(unittest.TestCase):
    def test_parse_pr_url(self):
        parsed = claude_review.parse_pr_url("https://github.com/requestly/requestly/pull/4718")

        self.assertEqual(parsed.owner, "requestly")
        self.assertEqual(parsed.repo, "requestly")
        self.assertEqual(parsed.number, 4718)
        self.assertEqual(parsed.diff_url, "https://github.com/requestly/requestly/pull/4718.diff")

    def test_parse_diff_counts_changed_files_and_lines(self):
        files = claude_review.parse_diff(SAMPLE_DIFF)

        self.assertEqual([change.path for change in files], ["app/auth/login.py", "tests/test_login.py"])
        self.assertEqual(sum(change.additions for change in files), 6)
        self.assertEqual(sum(change.deletions for change in files), 1)
        self.assertTrue(files[0].is_sensitive)
        self.assertTrue(files[1].is_test)

    def test_review_markdown_contains_required_sections(self):
        review = claude_review.build_review(SAMPLE_DIFF)
        markdown = review.to_markdown()

        self.assertIn("### Summary of Changes", markdown)
        self.assertIn("### Identified Risks", markdown)
        self.assertIn("### Improvement Suggestions", markdown)
        self.assertIn("### Confidence", markdown)
        self.assertRegex(markdown, r"\b(Low|Medium|High)\b")

    def test_no_tests_diff_reports_test_risk(self):
        diff = SAMPLE_DIFF.split("diff --git a/tests/test_login.py", 1)[0]
        review = claude_review.build_review(diff)

        self.assertTrue(any("No test file changed" in risk for risk in review.risks))
        self.assertTrue(any("regression test" in suggestion for suggestion in review.suggestions))


if __name__ == "__main__":
    unittest.main()
