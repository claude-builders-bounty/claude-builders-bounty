from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest


AGENT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_DIR))

import claude_review  # noqa: E402


CODE_ONLY_DIFF = """\
diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,4 @@
 def run():
-    return "ok"
+    value = "placeholder"
+    return value
"""

MIXED_RISK_DIFF = """\
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 1111111..2222222 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1,3 +1,4 @@
 name: CI
+permissions: write-all
diff --git a/package-lock.json b/package-lock.json
index 1111111..2222222 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,3 +1,4 @@
 {"lockfileVersion": 3}
+{"new": true}
diff --git a/secrets/example.env b/secrets/example.env
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/secrets/example.env
@@ -0,0 +1 @@
+VALUE=redacted
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_app():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url_accepts_canonical_pull_request_url(self) -> None:
        pr = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")

        self.assertEqual(pr.owner, "owner")
        self.assertEqual(pr.repo, "repo")
        self.assertEqual(pr.number, 123)
        self.assertEqual(pr.diff_url, "https://github.com/owner/repo/pull/123.diff")

    def test_parse_pr_url_rejects_non_pull_request_url(self) -> None:
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/owner/repo/issues/123")

    def test_code_without_tests_reports_test_risk(self) -> None:
        pr = claude_review.PullRequest("owner", "repo", 123)
        review = claude_review.analyze(pr, CODE_ONLY_DIFF)

        self.assertEqual(review.confidence, "Medium")
        self.assertTrue(any("without an obvious test file" in risk for risk in review.risks))
        self.assertTrue(any("focused tests" in suggestion for suggestion in review.suggestions))

    def test_mixed_risks_are_detected_from_paths(self) -> None:
        pr = claude_review.PullRequest("owner", "repo", 123)
        review = claude_review.analyze(pr, MIXED_RISK_DIFF)
        all_risks = "\n".join(review.risks)

        self.assertIn("Workflow or action configuration changed", all_risks)
        self.assertIn("Dependency lock or manifest files changed", all_risks)
        self.assertIn("credentials, secrets, or key material", all_risks)

    def test_markdown_contains_required_sections(self) -> None:
        pr = claude_review.PullRequest("owner", "repo", 123)
        markdown = claude_review.render_markdown(pr, claude_review.analyze(pr, MIXED_RISK_DIFF))

        self.assertIn("### Summary of Changes", markdown)
        self.assertIn("### Identified Risks", markdown)
        self.assertIn("### Improvement Suggestions", markdown)
        self.assertRegex(markdown, r"### Confidence Score: (Low|Medium|High)")

    def test_cli_can_review_local_diff_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            diff_path = tmp_path / "pr.diff"
            output_path = tmp_path / "review.md"
            diff_path.write_text(MIXED_RISK_DIFF, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_DIR / "claude_review.py"),
                    "--pr",
                    "https://github.com/owner/repo/pull/123",
                    "--diff-file",
                    str(diff_path),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## Claude PR Review", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
