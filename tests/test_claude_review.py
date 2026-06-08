import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "claude-review"
LOADER = importlib.machinery.SourceFileLoader("claude_review", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader("claude_review", LOADER)
claude_review = importlib.util.module_from_spec(SPEC)
sys.modules["claude_review"] = claude_review
SPEC.loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/src/auth.js b/src/auth.js
index 1111111..2222222 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -1,2 +1,4 @@
+export function requireRole(user, role) {
+  return user?.role === role;
+}
 export const ok = true;
diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Example
+Documented auth behavior.
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")

        self.assertEqual(ref.owner, "owner")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 123)

    def test_analyze_diff_counts_files_and_risks(self):
        stats = claude_review.analyze_diff(SAMPLE_DIFF)

        self.assertEqual(stats.files, ["src/auth.js", "README.md"])
        self.assertEqual(stats.code_files_changed, 1)
        self.assertEqual(stats.docs_files_changed, 1)
        self.assertEqual(stats.test_files_changed, 0)
        self.assertEqual(stats.security_sensitive_files, 1)

    def test_render_review_has_required_sections(self):
        review = claude_review.render_review(
            {
                "title": "Add auth helper",
                "user": {"login": "octocat"},
                "head": {"sha": "abcdef123456"},
            },
            SAMPLE_DIFF,
            "https://github.com/owner/repo/pull/123",
        )

        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertIn("### Confidence: Medium", review)
        self.assertIn("Runtime code changed without accompanying test files", review)
