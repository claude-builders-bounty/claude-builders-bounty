#!/usr/bin/env python3
"""
Unit test suite for claude_review.py (Claude Code PR Review Sub-Agent).

Covers:
  - GitHub PR URL validation and parsing
  - Unified diff parsing across multi-file, new-file, and deleted-file patches
  - Security & code-quality risk detection (hardcoded secrets, SQLi, shell=True, eval, bare except)
  - Missing test coverage detection when production files change without tests
  - Structured Markdown formatting (2-3 sentence summary, risks, suggestions, confidence score)
  - Mocked GitHub API & Anthropic Claude API integration and graceful fallback
  - CLI entrypoint flags (--diff, --format json/markdown, --output)
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure output directory is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claude_review


SAMPLE_RISKY_DIFF = """diff --git a/src/auth_service.py b/src/auth_service.py
new file mode 100644
index 0000000..e1b2c3d
--- /dev/null
+++ b/src/auth_service.py
@@ -0,0 +1,22 @@
+import os
+import subprocess
+
+API_KEY = "sk-live-1234567890abcdefghijklmnop"
+
+def authenticate_user(cursor, username, raw_cmd):
+    query = f"SELECT id, role FROM users WHERE username = '{username}'"
+    cursor.execute(query)
+    subprocess.run(raw_cmd, shell=True)
+    try:
+        result = eval("1 + 1")
+    except:
+        pass
+    return result
"""

SAMPLE_CLEAN_WITH_TESTS_DIFF = """diff --git a/src/math_utils.py b/src/math_utils.py
index 1111111..2222222 100644
--- a/src/math_utils.py
+++ b/src/math_utils.py
@@ -1,3 +1,6 @@
 def clamp(val: int, low: int, high: int) -> int:
+    if low > high:
+        raise ValueError("low bound cannot exceed high bound")
     return max(low, min(high, val))
diff --git a/tests/test_math_utils.py b/tests/test_math_utils.py
index 3333333..4444444 100644
--- a/tests/test_math_utils.py
+++ b/tests/test_math_utils.py
@@ -1,4 +1,8 @@
+import pytest
 from src.math_utils import clamp
 
 def test_clamp_bounds():
     assert clamp(5, 0, 10) == 5
+    with pytest.raises(ValueError):
+        clamp(5, 10, 0)
"""


class TestClaudeReviewAgent(unittest.TestCase):
    """Comprehensive unit tests for claude_review."""

    def test_parse_pr_url_valid(self):
        owner, repo, num = claude_review.parse_pr_url(
            "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/42/files"
        )
        self.assertEqual(owner, "claude-builders-bounty")
        self.assertEqual(repo, "claude-builders-bounty")
        self.assertEqual(num, 42)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/owner/repo/issues/42")

    def test_parse_unified_diff_counts(self):
        files = claude_review.parse_unified_diff(SAMPLE_CLEAN_WITH_TESTS_DIFF)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].display_path, "src/math_utils.py")
        self.assertEqual(len(files[0].added_lines), 2)
        self.assertEqual(files[1].display_path, "tests/test_math_utils.py")
        self.assertEqual(len(files[1].added_lines), 3)

    def test_static_analysis_detects_high_risks_and_missing_tests(self):
        result = claude_review.analyze_diff_statically(
            SAMPLE_RISKY_DIFF,
            pr_title="feat: add user authentication helper",
            pr_url="https://github.com/example/app/pull/101",
        )
        self.assertEqual(result.files_changed, 1)
        self.assertEqual(result.confidence, "High")

        joined_risks = "\n".join(result.risks)
        self.assertIn("Hardcoded Secret / Credential", joined_risks)
        self.assertIn("Command Injection / Unsafe Shell Execution", joined_risks)
        self.assertIn("Potential SQL Injection", joined_risks)
        self.assertIn("Dynamic Code Execution", joined_risks)
        self.assertIn("Broad / Bare Exception Handler", joined_risks)
        self.assertIn("Missing Test Coverage", joined_risks)

    def test_static_analysis_clean_patch_with_tests(self):
        result = claude_review.analyze_diff_statically(
            SAMPLE_CLEAN_WITH_TESTS_DIFF,
            pr_title="fix: validate bounds in clamp()",
        )
        self.assertEqual(result.files_changed, 2)
        self.assertEqual(len(result.risks), 0)
        md = result.to_markdown()
        self.assertIn("### Summary of Changes", md)
        self.assertIn("### Identified Risks", md)
        self.assertIn("### Improvement Suggestions", md)
        self.assertIn("### Confidence Score", md)
        self.assertIn("**Confidence Score: High**", md)

    def test_markdown_summary_has_two_to_three_sentences(self):
        result = claude_review.analyze_diff_statically(SAMPLE_RISKY_DIFF)
        self.assertGreaterEqual(len(result.summary_sentences), 2)
        self.assertLessEqual(len(result.summary_sentences), 3)

    def test_empty_diff_handling(self):
        result = claude_review.analyze_diff_statically("")
        self.assertEqual(result.files_changed, 0)
        self.assertEqual(result.confidence, "High")
        self.assertIn("Empty diff", "\n".join(result.risks))

    @mock.patch("urllib.request.urlopen")
    def test_fetch_github_pr_mocked(self, mock_urlopen):
        meta_resp = mock.MagicMock()
        meta_resp.read.return_value = json.dumps({"title": "Mocked PR Title"}).encode("utf-8")
        meta_resp.__enter__.return_value = meta_resp

        diff_resp = mock.MagicMock()
        diff_resp.read.return_value = SAMPLE_CLEAN_WITH_TESTS_DIFF.encode("utf-8")
        diff_resp.__enter__.return_value = diff_resp

        mock_urlopen.side_effect = [meta_resp, diff_resp]

        meta, diff_text = claude_review.fetch_github_pr("https://github.com/org/repo/pull/7")
        self.assertEqual(meta["title"], "Mocked PR Title")
        self.assertIn("src/math_utils.py", diff_text)

    @mock.patch("urllib.request.urlopen")
    def test_claude_api_enrichment_mocked(self, mock_urlopen):
        claude_payload = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "summary_sentences": [
                                "Adds bounds validation to the clamp helper.",
                                "Includes unit tests for invalid bound arguments.",
                            ],
                            "risks": ["**[Low] API Contract** (`src/math_utils.py:2`): Callers passing inverted bounds will now receive a ValueError."],
                            "suggestions": ["Document the ValueError exception in the clamp() docstring."],
                            "confidence": "High",
                            "confidence_reason": "Small, well-tested diff with clear semantics.",
                        }
                    ),
                }
            ]
        }
        api_resp = mock.MagicMock()
        api_resp.read.return_value = json.dumps(claude_payload).encode("utf-8")
        api_resp.__enter__.return_value = api_resp
        mock_urlopen.return_value = api_resp

        baseline = claude_review.analyze_diff_statically(SAMPLE_CLEAN_WITH_TESTS_DIFF)
        enriched = claude_review.analyze_with_claude_api(
            SAMPLE_CLEAN_WITH_TESTS_DIFF,
            static_baseline=baseline,
            api_key="test-key",
            model="claude-3-7-sonnet-latest",
        )
        self.assertEqual(enriched.confidence, "High")
        self.assertIn("claude", enriched.engine)
        self.assertIn("ValueError", enriched.risks[0])

    def test_cli_main_diff_file_and_json_output(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".diff", delete=False) as tmp_diff:
            tmp_diff.write(SAMPLE_RISKY_DIFF)
            diff_path = tmp_diff.name

        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp_out:
            out_path = tmp_out.name

        try:
            exit_code = claude_review.main(
                ["--diff", diff_path, "--format", "json", "--output", out_path]
            )
            self.assertEqual(exit_code, 0)
            with open(out_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["confidence_score"], "High")
            self.assertEqual(data["metrics"]["files_changed"], 1)
            self.assertGreaterEqual(len(data["identified_risks"]), 4)
        finally:
            os.remove(diff_path)
            os.remove(out_path)


if __name__ == "__main__":
    unittest.main()