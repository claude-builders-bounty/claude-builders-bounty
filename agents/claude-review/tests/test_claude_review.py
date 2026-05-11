from __future__ import annotations

import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bin" / "claude-review"

loader = importlib.machinery.SourceFileLoader("claude_review", str(MODULE_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
claude_review = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = claude_review
loader.exec_module(claude_review)


SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,4 @@
 print("hello")
+API_KEY = "sk-test"
+def handler():
+    return "ok"
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
    def test_parse_diff_counts_files_and_lines(self) -> None:
        files = claude_review.parse_diff(SAMPLE_DIFF)

        self.assertEqual([file.path for file in files], ["src/app.py", "tests/test_app.py"])
        self.assertEqual(files[0].additions, 3)
        self.assertEqual(files[0].deletions, 0)
        self.assertEqual(files[1].additions, 2)

    def test_risk_signals_detects_secrets(self) -> None:
        risks = claude_review.risk_signals(claude_review.parse_diff(SAMPLE_DIFF))

        self.assertTrue(any("credentials or secrets" in risk for risk in risks))

    def test_render_review_has_required_sections(self) -> None:
        review = claude_review.render_review(SAMPLE_DIFF)

        self.assertIn("### Summary", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertIn("### Confidence Score", review)

    def test_confidence_is_high_when_tests_changed(self) -> None:
        files = claude_review.parse_diff(SAMPLE_DIFF)

        self.assertTrue(claude_review.confidence(files).startswith("High"))

    def test_cli_requires_pr_for_post_comment(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--diff-file",
                str(ROOT / "samples" / "pr-61-review.md"),
                "--post-comment",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--post-comment requires --pr", completed.stderr)

    def test_cli_writes_output_for_diff_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_path = Path(temp_dir) / "sample.diff"
            output_path = Path(temp_dir) / "review.md"
            diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--diff-file",
                    str(diff_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            review = output_path.read_text(encoding="utf-8")
            self.assertIn("## PR Review", review)
            self.assertIn("Added lines look like they may contain hard-coded credentials", review)


if __name__ == "__main__":
    unittest.main()
