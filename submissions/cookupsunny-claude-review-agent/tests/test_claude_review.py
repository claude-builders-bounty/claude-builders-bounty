from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import claude_review  # noqa: E402


SAMPLE_DIFF = """diff --git a/app/auth.py b/app/auth.py
index 1111111..2222222 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,3 +1,8 @@
 def login(request):
-    return True
+    password = request.POST["password"]
+    token = "hardcoded-secret-token"
+    return check_password(password, token)
diff --git a/tests/test_auth.py b/tests/test_auth.py
index 3333333..4444444 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -0,0 +1,4 @@
+def test_login_rejects_bad_password():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self) -> None:
        ref = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(ref.owner, "owner")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 123)
        self.assertEqual(ref.diff_url, "https://github.com/owner/repo/pull/123.diff")

    def test_analyze_diff_collects_signals(self) -> None:
        analysis = claude_review.analyze_diff(SAMPLE_DIFF)
        self.assertEqual(len(analysis.files), 2)
        all_signals = set().union(*(item.signals for item in analysis.files))
        self.assertIn("possible-secret", all_signals)
        self.assertIn("auth", all_signals)
        self.assertIn("tests", all_signals)

    def test_static_review_has_required_sections(self) -> None:
        ref = claude_review.parse_pr_url("https://github.com/owner/repo/pull/123")
        review = claude_review.static_review(ref, claude_review.analyze_diff(SAMPLE_DIFF))
        self.assertTrue(claude_review.has_required_sections(review))
        self.assertIn("Possible hardcoded secret", review)

    def test_cli_offline_diff_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            diff_path = Path(tmpdir) / "pr.diff"
            diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "claude-review"),
                    "--pr",
                    "https://github.com/owner/repo/pull/123",
                    "--diff-file",
                    str(diff_path),
                    "--no-claude",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Summary", result.stdout)
        self.assertIn("## Confidence Score", result.stdout)


if __name__ == "__main__":
    unittest.main()
