import importlib.machinery
import importlib.util
import os
import sys
import unittest

CLI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin", "claude-review"))
loader = importlib.machinery.SourceFileLoader("claude_review", CLI_PATH)
spec = importlib.util.spec_from_loader("claude_review", loader)
claude_review = importlib.util.module_from_spec(spec)
sys.modules["claude_review"] = claude_review
loader.exec_module(claude_review)


class TestClaudeReviewAgent(unittest.TestCase):
    def test_parse_valid_pr_url(self):
        owner, repo, number = claude_review.parse_pr_url(
            "https://github.com/Parabola-org/parabola/pull/103"
        )
        self.assertEqual(owner, "Parabola-org")
        self.assertEqual(repo, "parabola")
        self.assertEqual(number, 103)

    def test_parse_invalid_pr_url_raises(self):
        with self.assertRaises(ValueError):
            claude_review.parse_pr_url("https://github.com/owner/repo/issues/10")

    def test_structured_markdown_output_sections(self):
        ctx = claude_review.PRContext(
            owner="Parabola-org",
            repo="parabola",
            number=103,
            title="fix(chains/stellar): distinguish RPC outages from missing recipient accounts",
            body="Fixes #4",
            author="Mannerless",
            base_ref="main",
            head_ref="fix/stellar-recipient-rpc-error",
            additions=42,
            deletions=8,
            changed_files=2,
            diff=(
                "--- a/src/chains/stellar.ts\n"
                "+++ b/src/chains/stellar.ts\n"
                "@@ -200,4 +200,9 @@\n"
                "+  try {\n"
                "+    account = await server.getAccount(recipient);\n"
                "+  } catch (err) {\n"
                "+    throw err;\n"
                "+  }\n"
            ),
            files=[
                {"filename": "src/chains/stellar.ts", "additions": 18, "deletions": 6},
                {"filename": "tests/stellar.test.ts", "additions": 24, "deletions": 2},
            ],
        )
        md = claude_review.analyze_diff_heuristically(ctx)
        self.assertIn("### Summary of Changes", md)
        self.assertIn("### Identified Risks", md)
        self.assertIn("### Improvement Suggestions", md)
        self.assertIn("### Confidence Score", md)
        self.assertRegex(md, r"\*\*Confidence Score: (Low|Medium|High)\*\*")


if __name__ == "__main__":
    unittest.main()
