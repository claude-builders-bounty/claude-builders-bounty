"""Offline tests for the claude-review CLI. Run: python -m unittest discover -s tests -v"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from importlib.machinery import SourceFileLoader

ROOT = Path(__file__).resolve().parent.parent
loader = SourceFileLoader("claude_review", str(ROOT / "claude-review"))
spec = importlib.util.spec_from_loader("claude_review", loader)
review = importlib.util.module_from_spec(spec)
sys.modules["claude_review"] = review
spec.loader.exec_module(review)

GOOD = """## Summary

Adds a changelog generator and installs it as a skill. It reads commits since the last tag and buckets them by conventional-commit prefix.

## Risks

- **medium** `generate-changelog.sh:88` — the `case` patterns are prefix-based, so a commit starting with `address` is classified as `add`.
  ```bash
  case "$lower" in
    feat*|add*|implement*)
  ```

## Suggestions

- `generate-changelog.sh:120` — use `git log --format` with a `%x00` separator so subjects containing tabs are not split.

## Confidence

**High** — the script is self-contained and every branch is visible in the diff.
"""

DIFF = """diff --git a/a.sh b/a.sh
index 1111111..2222222 100644
--- a/a.sh
+++ b/a.sh
@@ -1,3 +1,4 @@
 #!/usr/bin/env bash
+echo hello
 echo world
diff --git a/b.sh b/b.sh
new file mode 100644
--- /dev/null
+++ b/b.sh
@@ -0,0 +1,2 @@
+#!/usr/bin/env bash
+true
"""

BIG_DIFF = "\n".join(
    ["diff --git a/f0 b/f0", "--- a/f0", "+++ b/f0", "@@ -1 +1 @@", "-a", "+b"]
    + [f"diff --git a/f{i} b/f{i}\n--- a/f{i}\n+++ b/f{i}\n@@ -1 +1 @@\n-a\n+b" for i in range(1, 200)]
)


class UrlTests(unittest.TestCase):
    def test_parses_pr_url(self):
        self.assertEqual(review.parse_pr_url("https://github.com/acme/app/pull/42"), ("acme", "app", 42))

    def test_accepts_browser_urls_with_suffix(self):
        for suffix in ["", "/", "/files", "/commits"]:
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    review.parse_pr_url(f"https://github.com/acme/app/pull/7{suffix}"), ("acme", "app", 7)
                )

    def test_rejects_non_pr_url(self):
        for url in ["https://github.com/acme/app", "git@github.com:acme/app.git", "acme/app#1"]:
            with self.assertRaises(review.ReviewError):
                review.parse_pr_url(url)


class PromptTests(unittest.TestCase):
    def make_pr(self, diff: str = DIFF) -> dict:
        return {
            "owner": "acme",
            "repo": "app",
            "number": 42,
            "title": "Add thing",
            "body": "Closes #1",
            "author": "dev",
            "base": "main",
            "head": "feature",
            "additions": 3,
            "deletions": 1,
            "changed_files": 2,
            "files": [{"filename": "a.sh", "status": "modified", "additions": 1, "deletions": 0}],
            "diff": diff,
        }

    def test_prompt_contains_instructions_and_metadata(self):
        prompt = review.build_prompt(self.make_pr())
        self.assertIn("senior engineer", prompt)
        self.assertIn("acme/app", prompt)
        self.assertIn("#42", prompt)
        self.assertIn("## Output format", prompt)
        self.assertIn("```diff", prompt)
        self.assertIn("a.sh", prompt)

    def test_prompt_truncates_large_diff(self):
        prompt = review.build_prompt(self.make_pr(BIG_DIFF), max_diff_lines=60)
        self.assertIn("diff truncated", prompt)
        self.assertIn("Review only what is shown", prompt)

    def test_truncation_keeps_whole_files(self):
        text, omitted = review.truncate_diff(BIG_DIFF, 60)
        self.assertGreater(omitted, 0)
        self.assertTrue(text.rstrip().splitlines()[-1].startswith("[diff truncated") or "diff truncated" in text)
        # never ends in the middle of a hunk marker
        self.assertNotIn("@@@", text)

    def test_small_diff_is_untouched(self):
        text, omitted = review.truncate_diff(DIFF, 100)
        self.assertEqual(omitted, 0)
        self.assertEqual(text, DIFF)

    def test_long_description_is_capped(self):
        pr = self.make_pr()
        pr["body"] = "x" * 5000
        prompt = review.build_prompt(pr)
        self.assertIn("description truncated", prompt)


class OutputTests(unittest.TestCase):
    def test_clean_strips_markdown_fence(self):
        self.assertEqual(review.clean_review("```markdown\n## Summary\nhi\n```"), "## Summary\nhi")

    def test_valid_review_has_no_problems(self):
        self.assertEqual(review.validate_review(GOOD), [])

    def test_missing_sections_are_reported(self):
        problems = review.validate_review("## Summary\nonly this")
        self.assertTrue(any("Risks" in p for p in problems))
        self.assertTrue(any("Confidence" in p for p in problems))

    def test_confidence_must_be_a_known_level(self):
        bad = GOOD.replace("**High**", "**Probably fine**")
        self.assertTrue(any("confidence" in p.lower() for p in review.validate_review(bad)))


class MainTests(unittest.TestCase):
    def run_main(self, argv, claude_output=GOOD):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(review, "run_claude", return_value=claude_output), \
             mock.patch.object(review, "find_claude", return_value="claude"):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = review.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_offline_diff_produces_review_on_stdout(self):
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
            handle.write(DIFF)
            path = handle.name
        code, out, _ = self.run_main(["--diff-file", path, "--title", "Add thing"])
        self.assertEqual(code, 0)
        self.assertIn("## Summary", out)
        self.assertIn("## Confidence", out)
        Path(path).unlink()

    def test_output_file_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "x.diff"
            diff_path.write_text(DIFF, encoding="utf-8")
            out_path = Path(tmp) / "review.md"
            code, out, err = self.run_main(
                ["--diff-file", str(diff_path), "--output", str(out_path)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertIn("## Summary", out_path.read_text(encoding="utf-8"))
            self.assertIn("Review written", err)

    def test_invalid_review_returns_three(self):
        code, _, err = self.run_main(["--diff-file", "x.diff"], claude_output="looks fine to me")
        # missing input file is caught before the model call
        self.assertEqual(code, 1)
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
            handle.write(DIFF)
            path = handle.name
        code, _, err = self.run_main(["--diff-file", path], claude_output="looks fine to me")
        self.assertEqual(code, 3)
        self.assertIn("failed validation", err)
        Path(path).unlink()

    def test_dry_run_never_calls_the_model(self):
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
            handle.write(DIFF)
            path = handle.name
        with mock.patch.object(review, "run_claude", side_effect=AssertionError("model was called")):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = review.main(["--diff-file", path, "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("## Diff", out.getvalue())
        Path(path).unlink()

    def test_missing_input_is_a_clean_error(self):
        code, _, err = self.run_main(["--diff-file", "does-not-exist.diff"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_post_is_called_only_with_pr(self):
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
            handle.write(DIFF)
            path = handle.name
        with mock.patch.object(review, "post_review", return_value="https://example/1") as poster:
            code, _, _ = self.run_main(["--diff-file", path, "--post"])
        self.assertEqual(code, 1)  # --post requires --pr
        poster.assert_not_called()
        Path(path).unlink()

    def test_claude_bin_missing_gives_actionable_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
            handle.write(DIFF)
            path = handle.name
        with mock.patch.dict("os.environ", {"PATH": "", "CLAUDE_BIN": ""}, clear=False), \
             mock.patch.object(review.shutil, "which", return_value=None):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = review.main(["--diff-file", path])
        self.assertEqual(code, 1)
        self.assertIn("npm i -g @anthropic-ai/claude-code", err.getvalue())
        Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
