#!/usr/bin/env python3
"""Tests for claude-review.py — stdlib unittest only.

Run from the workspace root:
    python3 -m unittest discover -s agents/pr-review/tests -v
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# claude-review.py has a hyphen in its filename, so it cannot be imported
# as a normal module — load it by file path instead.
_CLI_PATH = Path(__file__).resolve().parent.parent / "claude-review.py"
_spec = importlib.util.spec_from_file_location("claude_review", _CLI_PATH)
cr = importlib.util.module_from_spec(_spec)
sys.modules["claude_review"] = cr  # dataclasses need the module registered
_spec.loader.exec_module(cr)


SMALL_DIFF = """\
diff --git a/app.py b/app.py
new file mode 100644
--- /dev/null
+++ b/app.py
@@ -0,0 +1,5 @@
+def greet(name):
+    return f"Hello, {name}"
+
+def add(a, b):
+    return a + b
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,3 @@
+def test_add():
+    assert add(1, 2) == 3
"""

RISKY_DIFF = """\
diff --git a/config.py b/config.py
new file mode 100644
--- /dev/null
+++ b/config.py
@@ -0,0 +1,6 @@
+API_KEY = "sk-live-abcdefghijklmnop1234"
+PASSWORD = "hunter2-secret"
+import os
+os.system("rm -rf /tmp/x")
+eval(user_input)
+result = subprocess.run(cmd, shell=True)
"""

DESTRUCTIVE_DIFF = """\
diff --git a/clean.sh b/clean.sh
new file mode 100644
--- /dev/null
+++ b/clean.sh
@@ -0,0 +1,3 @@
+rm -rf /var/data
+git push --force origin main
+DROP TABLE users;
"""


def ref(num=123):
    return cr.PRRef(owner="owner", repo="repo", number=num)


class TestParsePrUrl(unittest.TestCase):
    def test_plain_url(self):
        r = cr.parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual((r.owner, r.repo, r.number), ("owner", "repo", 123))

    def test_url_with_trailing_slash_and_query(self):
        r = cr.parse_pr_url("https://github.com/owner/repo/pull/123/files?x=1")
        self.assertEqual(r.number, 123)

    def test_pulls_plural(self):
        r = cr.parse_pr_url("https://github.com/a/b/pulls/7")
        self.assertEqual(r.number, 7)

    def test_diff_url_and_api_url(self):
        r = ref()
        self.assertEqual(r.diff_url, "https://github.com/owner/repo/pull/123.diff")
        self.assertIn("/repos/owner/repo/pulls/123", r.api_url)

    def test_rejects_issue_url(self):
        with self.assertRaises(ValueError):
            cr.parse_pr_url("https://github.com/owner/repo/issues/123")

    def test_rejects_garbage(self):
        for bad in ("", "not a url", "https://example.com/owner/repo/pull/1"):
            with self.assertRaises(ValueError, msg=bad):
                cr.parse_pr_url(bad)


class TestParseDiff(unittest.TestCase):
    def test_files_and_counts(self):
        files = cr.parse_diff(SMALL_DIFF)
        self.assertEqual([f.path for f in files], ["app.py", "tests/test_app.py"])
        self.assertEqual(files[0].additions, 5)
        self.assertEqual(files[0].deletions, 0)
        self.assertEqual(files[1].additions, 2)

    def test_added_lines_have_numbers(self):
        files = cr.parse_diff(SMALL_DIFF)
        self.assertEqual(files[0].added_lines[0][0], 1)
        self.assertIn("def greet", files[0].added_lines[0][1])

    def test_deletions_counted(self):
        diff = ("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n"
                "@@ -1,2 +1,1 @@\n-old()\n+new()\n")
        files = cr.parse_diff(diff)
        self.assertEqual(files[0].additions, 1)
        self.assertEqual(files[0].deletions, 1)

    def test_empty_diff(self):
        self.assertEqual(cr.parse_diff(""), [])

    def test_test_and_docs_detection(self):
        files = cr.parse_diff(SMALL_DIFF)
        self.assertTrue(files[1].is_test)
        self.assertFalse(files[0].is_test)
        self.assertTrue(cr.FileChange(path="README.md").is_docs)
        self.assertTrue(cr.FileChange(path="package-lock.json").is_lockfile)


class TestRisks(unittest.TestCase):
    def test_secrets_flagged(self):
        risks = cr.find_risks(cr.parse_diff(RISKY_DIFF))
        messages = " ".join(r[3] for r in risks)
        self.assertIn("API key", messages)
        self.assertIn("password", messages.lower())

    def test_destructive_flagged(self):
        risks = cr.find_risks(cr.parse_diff(DESTRUCTIVE_DIFF))
        messages = " ".join(r[3] for r in risks)
        self.assertIn("rm -rf", messages)
        self.assertIn("git push --force", messages)
        self.assertIn("DROP TABLE", messages)

    def test_eval_and_shell_flagged(self):
        risks = cr.find_risks(cr.parse_diff(RISKY_DIFF))
        messages = " ".join(r[3] for r in risks)
        self.assertIn("eval()", messages)
        self.assertIn("shell=True", messages)

    def test_clean_diff_has_no_risks(self):
        self.assertEqual(cr.find_risks(cr.parse_diff(SMALL_DIFF)), [])

    def test_risk_has_file_and_line(self):
        risks = cr.find_risks(cr.parse_diff(RISKY_DIFF))
        self.assertTrue(all(r[1] and r[2] for r in risks))
        self.assertTrue(all(r[0] in ("High", "Medium") for r in risks))

    def test_docstring_mention_not_flagged(self):
        diff = ("diff --git a/hook.py b/hook.py\n--- /dev/null\n+++ b/hook.py\n"
                '@@ -0,0 +1,5 @@\n+"""\n+Blocks rm -rf, DROP TABLE and git push --force.\n+"""\n+def check(cmd):\n+    return True\n')
        self.assertEqual(cr.find_risks(cr.parse_diff(diff)), [])

    def test_readme_mention_not_flagged(self):
        diff = ("diff --git a/README.md b/README.md\n--- /dev/null\n+++ b/README.md\n"
                "@@ -0,0 +1,3 @@\n+# Hook\n+Blocks `rm -rf` and `DROP TABLE`.\n+Run `git push --force` to test the block.\n")
        self.assertEqual(cr.find_risks(cr.parse_diff(diff)), [])

    def test_test_file_string_not_flagged(self):
        diff = ("diff --git a/tests/test_hook.py b/tests/test_hook.py\n--- /dev/null\n+++ b/tests/test_hook.py\n"
                '@@ -0,0 +1,2 @@\n+assert check("rm -rf /tmp/x") == "blocked"\n'
                '+assert check("DROP TABLE users") == "blocked"\n')
        self.assertEqual(cr.find_risks(cr.parse_diff(diff)), [])

    def test_secret_in_docs_still_flagged(self):
        diff = ("diff --git a/README.md b/README.md\n--- /dev/null\n+++ b/README.md\n"
                '@@ -0,0 +1,1 @@\n+API_KEY = "sk-live-abcdefghijklmnop1234"\n')
        risks = cr.find_risks(cr.parse_diff(diff))
        self.assertTrue(any("API key" in r[3] for r in risks))

    def test_real_shell_rm_flagged(self):
        diff = ("diff --git a/clean.sh b/clean.sh\n--- /dev/null\n+++ b/clean.sh\n"
                "@@ -0,0 +1,1 @@\n+rm -rf /var/data\n")
        risks = cr.find_risks(cr.parse_diff(diff))
        self.assertTrue(any("rm -rf" in r[3] for r in risks))

    def test_error_message_string_not_flagged(self):
        diff = ("diff --git a/hook.py b/hook.py\n--- /dev/null\n+++ b/hook.py\n"
                '@@ -0,0 +1,2 @@\n+def reason():\n'
                '+    return "git push --force is blocked"\n')
        self.assertEqual(cr.find_risks(cr.parse_diff(diff)), [])

    def test_force_with_lease_not_flagged(self):
        diff = ("diff --git a/x.sh b/x.sh\n--- /dev/null\n+++ b/x.sh\n"
                "@@ -0,0 +1,1 @@\n+git push --force-with-lease origin main\n")
        self.assertEqual(cr.find_risks(cr.parse_diff(diff)), [])

    def test_delete_with_where_not_flagged(self):
        # DELETE with WHERE on the same statement is not a bare DELETE.
        diff = ("diff --git a/x.sql b/x.sql\n--- /dev/null\n+++ b/x.sql\n"
                "@@ -0,0 +1,1 @@\n+DELETE FROM users WHERE id = 1;\n")
        risks = cr.find_risks(cr.parse_diff(diff))
        self.assertFalse(any("DELETE FROM" in r[3] for r in risks))


class TestConfidenceAndSuggestions(unittest.TestCase):
    def test_small_tested_diff_is_high(self):
        files = cr.parse_diff(SMALL_DIFF)
        self.assertEqual(cr.confidence_for(files, [], meta_ok=True), "High")

    def test_no_tests_drops_to_medium(self):
        files = cr.parse_diff(SMALL_DIFF)
        files = [f for f in files if not f.is_test]
        self.assertEqual(cr.confidence_for(files, [], meta_ok=True), "Medium")

    def test_high_risk_drops_to_low(self):
        files = cr.parse_diff(RISKY_DIFF)
        risks = cr.find_risks(files)
        self.assertEqual(cr.confidence_for(files, risks, meta_ok=True), "Low")

    def test_large_diff_drops_to_low(self):
        big = cr.FileChange(path="big.py", additions=1200, deletions=0)
        self.assertEqual(cr.confidence_for([big], [], meta_ok=True), "Low")

    def test_empty_diff_is_low(self):
        self.assertEqual(cr.confidence_for([], [], meta_ok=True), "Low")

    def test_suggestions_ask_for_tests(self):
        files = [cr.FileChange(path="app.py", additions=10)]
        suggestions = cr.find_suggestions(files, [])
        self.assertTrue(any("test" in s.lower() for s in suggestions))

    def test_suggestions_flag_high_risks_first(self):
        files = cr.parse_diff(RISKY_DIFF)
        risks = cr.find_risks(files)
        suggestions = cr.find_suggestions(files, risks)
        self.assertIn("high-severity", suggestions[0].lower())

    def test_non_english_docs_suggestion(self):
        f = cr.FileChange(path="README.md", additions=3)
        f.added_lines = [(1, "# 你好"), (2, "这是一个中文说明" * 10),
                         (3, "更多中文内容" * 10)]
        suggestions = cr.find_suggestions([f], [])
        self.assertTrue(any("non-English" in s for s in suggestions))

    def test_english_docs_no_language_suggestion(self):
        files = cr.parse_diff(SMALL_DIFF)
        suggestions = cr.find_suggestions(files, [])
        self.assertFalse(any("non-English" in s for s in suggestions))

    def test_clean_small_pr_gets_generic_suggestion(self):
        files = cr.parse_diff(SMALL_DIFF)
        suggestions = cr.find_suggestions(files, [])
        self.assertTrue(suggestions)
        self.assertFalse(any("test" in s.lower() for s in suggestions))


class TestMarkdown(unittest.TestCase):
    def review(self, diff=SMALL_DIFF):
        return cr.review_diff(ref(), diff, {"title": "Add greet", "author": "alice"})

    def test_all_required_sections_present(self):
        md = self.review().markdown
        for heading in ("### 📋 Summary", "### ⚠️ Identified Risks",
                        "### 💡 Improvement Suggestions", "### ✅ Confidence:"):
            self.assertIn(heading, md, heading)
        self.assertIn("## 🤖 Claude Code Review", md)

    def test_summary_is_two_to_three_sentences(self):
        review = self.review()
        sentences = [s for s in review.summary.split(". ") if s.strip()]
        self.assertGreaterEqual(len(sentences), 2)
        self.assertLessEqual(len(sentences), 3)

    def test_confidence_in_markdown_matches(self):
        review = self.review()
        self.assertIn(f"### ✅ Confidence: {review.confidence}", review.markdown)

    def test_risks_appear_in_markdown(self):
        review = cr.review_diff(ref(), RISKY_DIFF, {})
        self.assertIn("API key", review.markdown)
        self.assertIn("config.py", review.markdown)

    def test_files_table_lists_every_file(self):
        md = self.review().markdown
        self.assertIn("`app.py`", md)
        self.assertIn("`tests/test_app.py`", md)

    def test_json_format_is_valid(self):
        review = self.review()
        data = json.loads(cr.render_json(
            ref(), {"title": "t"}, review.files, review.risks,
            review.suggestions, review.confidence, review.summary))
        self.assertEqual(data["confidence"], review.confidence)
        self.assertEqual(data["pr"], ref().html_url)


class TestCli(unittest.TestCase):
    def test_diff_file_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "changes.diff"
            diff_path.write_text(SMALL_DIFF, encoding="utf-8")
            out_path = Path(tmp) / "review.md"
            rc = cr.main(["--pr", "https://github.com/owner/repo/pull/123",
                          "--diff-file", str(diff_path),
                          "--output", str(out_path)])
            self.assertEqual(rc, 0)
            text = out_path.read_text(encoding="utf-8")
            # --diff-file mode has no PR metadata, so confidence is
            # Medium, not High — that is the documented calibration.
            self.assertIn("### ✅ Confidence: Medium", text)
            self.assertIn("app.py", text)

    def test_bad_url_exits_2(self):
        self.assertEqual(cr.main(["--pr", "not-a-url"]), 2)

    def test_missing_diff_file_exits_2(self):
        self.assertEqual(
            cr.main(["--pr", "https://github.com/owner/repo/pull/1",
                     "--diff-file", "/nonexistent.diff"]), 2)

    def test_post_without_token_refuses(self):
        with self.assertRaises(RuntimeError):
            old = os.environ.pop("GITHUB_TOKEN", None)
            try:
                cr.post_comment(ref(), "hello")
            finally:
                if old is not None:
                    os.environ["GITHUB_TOKEN"] = old


if __name__ == "__main__":
    unittest.main()
