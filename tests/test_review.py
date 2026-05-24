import unittest

from claude_review.github import PullRequestData, PullRequestRef, parse_pr_url
from claude_review.review import render_review


SIMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
 def hello():
-    return "hi"
+    return "hello"
+
+print(hello())
"""

TEST_DIFF = """diff --git a/src/auth.py b/src/auth.py
index 1111111..2222222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,2 +1,2 @@
-TOKEN_TTL = 60
+TOKEN_TTL = 120
diff --git a/tests/test_auth.py b/tests/test_auth.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/test_auth.py
@@ -0,0 +1,2 @@
+def test_token_ttl():
+    assert True
"""


class ReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = parse_pr_url("https://github.com/owner/repo/pull/123")
        self.assertEqual(ref.owner, "owner")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 123)

    def test_review_flags_code_without_tests(self):
        markdown = render_review(self._pr(SIMPLE_DIFF, additions=3, deletions=1))
        self.assertIn("# Claude Review", markdown)
        self.assertIn("Code changed without obvious test updates", markdown)
        self.assertIn("## Confidence\nHigh", markdown)

    def test_review_recognizes_security_sensitive_change_with_tests(self):
        markdown = render_review(self._pr(TEST_DIFF, additions=3, deletions=1, changed_files=2))
        self.assertIn("Security-sensitive paths", markdown)
        self.assertNotIn("Code changed without obvious test updates", markdown)
        self.assertIn("## Confidence\nMedium", markdown)

    def _pr(self, diff, additions=0, deletions=0, changed_files=1):
        return PullRequestData(
            ref=PullRequestRef(
                owner="example",
                repo="repo",
                number=1,
                url="https://github.com/example/repo/pull/1",
            ),
            title="Example PR",
            body="Adds a small change.",
            author="alice",
            base_ref="main",
            head_ref="feature",
            state="OPEN",
            is_draft=False,
            additions=additions,
            deletions=deletions,
            changed_files=changed_files,
            diff=diff,
            fetch_source="fixture",
        )


if __name__ == "__main__":
    unittest.main()
