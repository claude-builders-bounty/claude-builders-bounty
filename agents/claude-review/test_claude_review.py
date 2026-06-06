import importlib.util
import importlib.machinery
import sys
import unittest
from pathlib import Path


CLI = Path(__file__).with_name("claude-review")


def load_cli():
    loader = importlib.machinery.SourceFileLoader("claude_review", str(CLI))
    spec = importlib.util.spec_from_loader("claude_review", loader)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["claude_review"] = module
    spec.loader.exec_module(module)
    return module


class ClaudeReviewTests(unittest.TestCase):
    def setUp(self):
        self.cli = load_cli()

    def test_parse_pr_url(self):
        self.assertEqual(
            self.cli.parse_pr_url("https://github.com/owner/repo/pull/123"),
            ("owner", "repo", "123"),
        )

    def test_render_review_contract(self):
        pr = self.cli.PullRequest(
            owner="owner",
            repo="repo",
            number="123",
            title="Add tests",
            author="alice",
            changed_files=1,
            additions=10,
            deletions=1,
            diff="diff --git a/test_app.py b/test_app.py\n+++ b/test_app.py\n+def test_app():\n+    assert True\n",
        )

        output = self.cli.render_review(pr)
        self.assertIn("### Summary", output)
        self.assertIn("### Identified Risks", output)
        self.assertIn("### Improvement Suggestions", output)
        self.assertIn("### Confidence:", output)


if __name__ == "__main__":
    unittest.main()
