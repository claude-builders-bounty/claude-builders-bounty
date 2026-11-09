#!/usr/bin/env python3
"""Tests for claude_review.py. Run: python3 tests/test_claude_review.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import claude_review as cr  # noqa: E402

SECRET_DIFF = """\
diff --git a/app/config.py b/app/config.py
--- a/app/config.py
+++ b/app/config.py
@@ -1,2 +1,4 @@
 import os
+API_KEY = "sk-live-1234567890abcdef"
+conn = db.execute("SELECT * FROM users WHERE id = %s" % uid)
 DEBUG = False
"""

CLEAN_DOCS_DIFF = """\
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,1 +1,3 @@
 # Project
+Now with installation instructions.
+And a usage section.
"""

CODE_NO_TESTS_DIFF = """\
diff --git a/src/payments.py b/src/payments.py
--- a/src/payments.py
+++ b/src/payments.py
@@ -10,3 +10,8 @@ def charge(card, amount):
     return gateway.charge(card, amount)
+def refund(txn):
+    result = subprocess.run(cmd, shell=True)
+    print("refunding", txn)
+    return result
"""

MIGRATION_DEP_DIFF = """\
diff --git a/db/migrations/004_add_users.py b/db/migrations/004_add_users.py
--- a/db/migrations/004_add_users.py
+++ b/db/migrations/004_add_users.py
@@ -0,0 +1,4 @@
+def upgrade():
+    op.execute("DROP TABLE sessions")
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 flask==2.0
+requests==2.31.0
"""


class ParseTests(unittest.TestCase):
    def test_parse_counts(self):
        files = cr.parse_diff(SECRET_DIFF)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].path, "app/config.py")
        self.assertEqual(files[0].added, 2)
        self.assertEqual(files[0].removed, 0)

    def test_parse_pr_url(self):
        self.assertEqual(
            cr.parse_pr_url("https://github.com/o/r/pull/42"), ("o", "r", 42))
        with self.assertRaises(ValueError):
            cr.parse_pr_url("https://example.com/o/r/pull/42")


class DetectionTests(unittest.TestCase):
    def test_secret_and_sqli_flagged_high(self):
        files = cr.parse_diff(SECRET_DIFF)
        findings = cr.scan_lines(files)
        highs = [f.message for f in findings if f.severity == "high"]
        self.assertTrue(any("credential" in m or "secret" in m
                            for m in highs), highs)
        self.assertTrue(any("SQL" in m for m in highs), highs)

    def test_shell_true_and_debug_flagged(self):
        files = cr.parse_diff(CODE_NO_TESTS_DIFF)
        findings = cr.scan_lines(files)
        msgs = [f.message for f in findings]
        self.assertTrue(any("shell=True" in m for m in msgs), msgs)
        self.assertTrue(any("debug leftover" in m for m in msgs), msgs)

    def test_migration_and_dependency_structural(self):
        files = cr.parse_diff(MIGRATION_DEP_DIFF)
        findings = cr.structural_findings(files)
        msgs = " ".join(f.message for f in findings)
        self.assertIn("migration", msgs.lower())
        self.assertIn("Dependency", msgs)


class ReportTests(unittest.TestCase):
    def test_markdown_has_all_required_sections(self):
        out = cr.review_diff(SECRET_DIFF, title="Add config",
                             url="https://github.com/o/r/pull/1")
        for section in ("### Summary", "### Identified risks",
                        "### Improvement suggestions",
                        "### Confidence score"):
            self.assertIn(section, out)

    def test_clean_docs_pr_is_low_risk_high_confidence(self):
        out = cr.review_diff(CLEAN_DOCS_DIFF, title="Docs")
        self.assertIn("No high-signal risks detected", out)
        self.assertIn("**High**", out)

    def test_code_without_tests_gets_test_suggestion(self):
        out = cr.review_diff(CODE_NO_TESTS_DIFF, title="Add refund")
        self.assertIn("Add or update tests", out)

    def test_empty_diff_low_confidence(self):
        out = cr.review_diff("", title="Nothing")
        self.assertIn("**Low**", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
