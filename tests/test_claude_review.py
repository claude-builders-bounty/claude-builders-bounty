#!/usr/bin/env python3
"""
Unit Test Suite for Claude Code PR Reviewer Sub-Agent
Validates acceptance criteria compliance for Bounty #4 ($150).
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_PATH = Path(__file__).parent.parent / "agents" / "pr-reviewer" / "claude_review.py"


class TestClaudePRReviewer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert SCRIPT_PATH.exists(), f"Agent script not found at {SCRIPT_PATH}"

    def test_url_pattern_validation(self):
        # Import regex pattern from script
        sys.path.insert(0, str(SCRIPT_PATH.parent))
        from claude_review import PR_URL_PATTERN

        valid_urls = [
            "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5055",
            "http://github.com/owner/repo/pull/1",
            "https://github.com/my-org/project_x/pull/999/",
        ]
        for url in valid_urls:
            self.assertIsNotNone(PR_URL_PATTERN.match(url), f"Failed to match valid URL: {url}")

        invalid_urls = [
            "https://github.com/owner/repo",
            "https://gitlab.com/owner/repo/merge_requests/1",
            "not_a_url",
        ]
        for url in invalid_urls:
            self.assertIsNone(PR_URL_PATTERN.match(url), f"Matched invalid URL: {url}")

    def test_local_diff_review(self):
        sample_diff = """--- a/src/app.py
+++ b/src/app.py
@@ -10,3 +10,4 @@
 def handle_request():
+    token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
+    return "OK"
"""
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as tf:
            tf.write(sample_diff)
            temp_path = tf.name

        try:
            res = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--diff", temp_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(res.returncode, 0, f"Diff review failed: {res.stderr}")
            output = res.stdout
            self.assertIn("### Summary of Changes", output)
            self.assertIn("### Identified Risks", output)
            self.assertIn("### Improvement Suggestions", output)
            self.assertIn("### Confidence Score", output)
            # Must detect hardcoded secret
            self.assertIn("Hardcoded Secret / Token", output)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_sample_outputs_exist_and_non_empty(self):
        samples_dir = SCRIPT_PATH.parent / "samples"
        self.assertTrue(samples_dir.exists(), "samples/ directory must exist")
        sample_files = list(samples_dir.glob("*.md"))
        self.assertGreaterEqual(len(sample_files), 2, "Must contain at least 2 real PR review samples")
        for sample in sample_files:
            content = sample.read_text(encoding="utf-8")
            self.assertIn("### Summary of Changes", content)
            self.assertIn("### Identified Risks", content)
            self.assertIn("### Confidence Score", content)


if __name__ == "__main__":
    unittest.main()
