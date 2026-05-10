import unittest

from pr_reviewer.cli import parse_diff, review_diff


class ReviewDiffTests(unittest.TestCase):
    def test_code_without_tests_flags_test_risk(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 def hello():
-    return "hi"
+    return "hello"
+    print("changed")
"""
        review = review_diff(diff, "local")

        self.assertEqual(len(review.files), 1)
        self.assertEqual(review.files[0].additions, 2)
        self.assertTrue(any("without accompanying test" in risk for risk in review.risks))
        self.assertEqual(review.confidence, "Medium")

    def test_docs_only_review_has_high_confidence(self):
        diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Project
+More setup notes.
"""
        review = review_diff(diff, "local")

        self.assertEqual(review.confidence, "High")
        self.assertTrue(any("documentation" in risk for risk in review.risks))

    def test_secret_like_line_is_flagged(self):
        diff = """diff --git a/config.yml b/config.yml
--- a/config.yml
+++ b/config.yml
@@ -1 +1,2 @@
 name: app
+api_key: abcdefgh1234567890
"""
        review = review_diff(diff, "local")

        self.assertTrue(any("secrets or credentials" in risk for risk in review.risks))

    def test_parse_deleted_file(self):
        diff = """diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1 +0,0 @@
-print("bye")
"""
        files = parse_diff(diff)

        self.assertEqual(files[0].status, "deleted")
        self.assertEqual(files[0].deletions, 1)


if __name__ == "__main__":
    unittest.main()
