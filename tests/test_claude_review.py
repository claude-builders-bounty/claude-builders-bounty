import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.machinery
loader = importlib.machinery.SourceFileLoader("claude_review", str(ROOT / "claude-review"))
claude_review = loader.load_module()


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        self.assertEqual(
            claude_review.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )
        with self.assertRaises(SystemExit):
            claude_review.parse_pr_url("https://example.com/nope")

    def test_markdown_contains_required_sections(self):
        pr = claude_review.PRInfo(
            owner="owner",
            repo="repo",
            number="123",
            title="Add feature",
            author="alice",
            additions=12,
            deletions=3,
            changed_files=2,
            diff="""diff --git a/app.py b/app.py
+def run():
+    print('hi')
diff --git a/tests/test_app.py b/tests/test_app.py
+def test_run():
+    assert True
""",
        )
        out = claude_review.markdown_review(pr)
        self.assertIn("### Summary of changes", out)
        self.assertIn("### Identified risks", out)
        self.assertIn("### Improvement suggestions", out)
        self.assertIn("### Confidence score", out)
        self.assertRegex(out, r"\*\*(Low|Medium|High)\*\*")

    def test_flags_delete_without_where(self):
        pr = claude_review.PRInfo(
            owner="owner",
            repo="repo",
            number="1",
            additions=1,
            deletions=0,
            changed_files=1,
            diff="diff --git a/migration.sql b/migration.sql\n+DELETE FROM users;\n",
        )
        out = claude_review.markdown_review(pr)
        self.assertIn("Database/schema change", out)
        self.assertIn("No obvious test updates", out)

    def test_flags_force_sensitive_patterns(self):
        pr = claude_review.PRInfo(
            owner="owner",
            repo="repo",
            number="2",
            additions=2,
            deletions=0,
            changed_files=1,
            diff="diff --git a/run.py b/run.py\n+import subprocess\n+subprocess.run(cmd, shell=True)\n",
        )
        out = claude_review.markdown_review(pr)
        self.assertIn("Shell/process execution", out)


if __name__ == "__main__":
    unittest.main()
