import importlib.util
import importlib.machinery
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "bin" / "claude-review"
loader = importlib.machinery.SourceFileLoader("claude_review", str(CLI_PATH))
spec = importlib.util.spec_from_loader("claude_review", loader)
claude_review = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["claude_review"] = claude_review
spec.loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/app/auth.py b/app/auth.py
index 1111111..2222222 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,4 +1,7 @@
 def login(user, password):
+    api_key = "abc123"
+    if password == "":
+        return True
     return check_password(user, password)
diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Demo
+Updated docs.
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_github_pr_url(self):
        pr = claude_review.parse_pr_url("https://github.com/acme/project/pull/42")
        self.assertEqual(pr.owner, "acme")
        self.assertEqual(pr.repo, "project")
        self.assertEqual(pr.number, 42)

    def test_parse_owner_repo_shorthand(self):
        pr = claude_review.parse_pr_url("acme/project#42")
        self.assertEqual(pr.url, "https://github.com/acme/project/pull/42")

    def test_summarize_diff_counts_files_and_lines(self):
        summary = claude_review.summarize_diff(
            SAMPLE_DIFF,
            source="sample",
            truncated=False,
        )
        self.assertEqual(len(summary.files), 2)
        self.assertEqual(summary.additions, 4)
        self.assertEqual(summary.deletions, 0)

    def test_heuristic_review_has_required_sections(self):
        summary = claude_review.summarize_diff(
            SAMPLE_DIFF,
            source="sample",
            truncated=False,
        )
        review = claude_review.heuristic_review(SAMPLE_DIFF, summary)
        for section in claude_review.REQUIRED_SECTIONS:
            self.assertIn(f"## {section}", review)
        self.assertRegex(review, r"## Confidence Score\n(?:Low|Medium|High)")

    def test_risk_detection_flags_security_and_missing_tests(self):
        summary = claude_review.summarize_diff(
            SAMPLE_DIFF,
            source="sample",
            truncated=False,
        )
        risks = claude_review.find_risks(SAMPLE_DIFF, summary)
        joined = "\n".join(risks)
        self.assertIn("Application code changed without nearby test changes", joined)
        self.assertIn("Security-sensitive paths changed", joined)
        self.assertIn("Hard-coded API key-like value", joined)


if __name__ == "__main__":
    unittest.main()
