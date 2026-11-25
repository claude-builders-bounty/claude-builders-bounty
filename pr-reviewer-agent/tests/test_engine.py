"""Unit tests for the claude-review rule-based engine.

Run:  python3 -m unittest discover -s tests -v
No network access needed — all tests use inline diffs.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.machinery import SourceFileLoader

cr = SourceFileLoader("claude_review", os.path.join(
    os.path.dirname(__file__), "..", "claude-review")).load_module()


def review_for(diff, title="Test PR", body="Does a thing."):
    meta = {"title": title, "body": body}
    return cr.rule_based_review(meta, cr.parse_diff(diff))


class TestPrUrlParsing(unittest.TestCase):
    def test_standard_url(self):
        self.assertEqual(
            cr.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", 123))

    def test_pulls_variant_and_trailing_slash(self):
        self.assertEqual(
            cr.parse_pr_url("https://github.com/owner/repo/pulls/7/"),
            ("owner", "repo", 7))

    def test_bad_url(self):
        with self.assertRaises(ValueError):
            cr.parse_pr_url("https://github.com/owner/repo/issues/1")


class TestDiffParsing(unittest.TestCase):
    DIFF = """diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,3 @@
+import os
+print("hi")
+
diff --git a/old.py b/old.py
--- a/old.py
+++ b/old.py
@@ -1,2 +1,2 @@
-old()
+new()
"""

    def test_files_and_counts(self):
        files = cr.parse_diff(self.DIFF)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["status"], "added")
        self.assertEqual(files[0]["additions"], 3)
        self.assertEqual(files[1]["additions"], 1)
        self.assertEqual(files[1]["deletions"], 1)


class TestContextAwareness(unittest.TestCase):
    """The engine must not flag a security tool for the patterns it blocks."""

    def test_blocklist_strings_are_not_risks(self):
        diff = """diff --git a/hook.py b/hook.py
new file mode 100644
--- /dev/null
+++ b/hook.py
@@ -0,0 +1,5 @@
+BLOCKED = [r'\\brm\\s+-rf\\b', "DROP TABLE", 'git push --force']
+if re.search(BLOCKED[0], cmd):
+    block(cmd)
"""
        review = review_for(diff)
        self.assertNotIn("rm -rf", " ".join(review["risks"]))

    def test_docstring_lists_are_not_risks(self):
        diff = '''diff --git a/hook.py b/hook.py
new file mode 100644
--- /dev/null
+++ b/hook.py
@@ -0,0 +1,8 @@
+"""Hook that blocks:
+
+- rm -rf
+- DROP TABLE
+- git push --force
+"""
+import re
'''
        review = review_for(diff)
        self.assertNotIn("rm -rf", " ".join(review["risks"]))
        self.assertNotIn("DROP TABLE", " ".join(review["risks"]))

    def test_comment_mentions_are_not_risks(self):
        diff = """diff --git a/x.py b/x.py
new file mode 100644
--- /dev/null
+++ b/x.py
@@ -0,0 +1,2 @@
+# NOTE: this must never run rm -rf on user input
+safe = True
"""
        review = review_for(diff)
        self.assertNotIn("rm -rf", " ".join(review["risks"]))

    def test_real_execution_still_flags(self):
        diff = """diff --git a/x.py b/x.py
new file mode 100644
--- /dev/null
+++ b/x.py
@@ -0,0 +1,2 @@
+subprocess.run("rm -rf /tmp/data", shell=True)
"""
        review = review_for(diff)
        self.assertIn("rm -rf", " ".join(review["risks"]))
        self.assertEqual(review["confidence"], "Low")

    def test_eval_flags(self):
        diff = """diff --git a/x.py b/x.py
new file mode 100644
--- /dev/null
+++ b/x.py
@@ -0,0 +1,2 @@
+result = eval(user_input)
"""
        review = review_for(diff)
        self.assertTrue(any("eval" in r for r in review["risks"]))


class TestSecrets(unittest.TestCase):
    def test_github_token_flagged(self):
        diff = """diff --git a/x.py b/x.py
new file mode 100644
--- /dev/null
+++ b/x.py
@@ -0,0 +1,2 @@
+token = "ghp_abcdefghij1234567890"
"""
        review = review_for(diff)
        self.assertTrue(any("Secret" in r for r in review["risks"]))
        self.assertEqual(review["confidence"], "Low")


class TestReviewShape(unittest.TestCase):
    def test_all_four_sections_present(self):
        review = review_for(
            "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x\n+y\n")
        for key in ("summary", "risks", "suggestions", "confidence"):
            self.assertIn(key, review)
        self.assertIn(review["confidence"], ("Low", "Medium", "High"))

    def test_missing_tests_flagged(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 import os
+do_thing()
"""
        review = review_for(diff)
        self.assertTrue(any("no test" in r.lower() for r in review["risks"]))

    def test_tests_present_not_flagged(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 import os
+do_thing()
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_do_thing():
+    assert True
"""
        review = review_for(diff)
        self.assertFalse(any("no test" in r.lower() for r in review["risks"]))


if __name__ == "__main__":
    unittest.main()
