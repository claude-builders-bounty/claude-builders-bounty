import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
import subprocess

import claude_review


DIFF = """diff --git a/src/review.py b/src/review.py
index 1111111..2222222 100644
--- a/src/review.py
+++ b/src/review.py
@@ -1,2 +1,8 @@
+def review(value):
+    if value is None:
+        return ""
+    return value.strip()
diff --git a/tests/test_review.py b/tests/test_review.py
new file mode 100644
--- /dev/null
+++ b/tests/test_review.py
@@ -0,0 +1,2 @@
+def test_review():
+    assert True
"""


class ReviewTests(unittest.TestCase):
    def test_diff_stats_and_offline_contract(self):
        self.assertEqual(claude_review.diff_stats(DIFF), (6, 0, 2))
        output = claude_review.offline_review(DIFF, "Example")
        self.assertEqual(
            [line for line in output.splitlines() if line.startswith("## ")],
            ["## Summary", "## Risks", "## Suggestions", "## Confidence"],
        )
        self.assertRegex(output, r"## Confidence\n(?:High|Medium|Low)\b")
        self.assertEqual(claude_review.validate_review(output), output)

    def test_parse_pr_url_rejects_non_github(self):
        with self.assertRaises(claude_review.ReviewError):
            claude_review.parse_pr_url("https://example.com/a/b/pull/1")

    def test_cli_offline_from_stdin(self):
        out = io.StringIO()
        with patch("sys.stdin", io.TextIOWrapper(io.BytesIO(DIFF.encode()), encoding="utf-8")), redirect_stdout(out):
            self.assertEqual(claude_review.main(["--diff", "-", "--offline"]), 0)
        self.assertIn("## Summary", out.getvalue())

    def test_claude_output_is_validated(self):
        with self.assertRaises(claude_review.ReviewError):
            claude_review.validate_review("not a structured review")

    @patch("claude_review.shutil.which", return_value="claude")
    @patch("claude_review.subprocess.run")
    def test_claude_command_is_non_interactive_and_read_only(self, run, _which):
        run.return_value = subprocess.CompletedProcess(
            ["claude"],
            0,
            stdout="## Summary\nOkay.\n\n## Risks\n- None.\n\n## Suggestions\n- None.\n\n## Confidence\nHigh\n",
            stderr="",
        )
        output = claude_review.run_claude("review this", "claude")
        self.assertIn("## Confidence", output)
        command = run.call_args.args[0]
        self.assertEqual(command[0:3], ["claude", "-p", "Review the PR data provided on stdin and follow its exact output contract."])
        self.assertIn("--permission-mode", command)
        self.assertIn("plan", command)
        self.assertEqual(run.call_args.kwargs["input"], "review this")


if __name__ == "__main__":
    unittest.main()
