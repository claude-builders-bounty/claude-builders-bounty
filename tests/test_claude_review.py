import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "claude_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("claude_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ClaudeReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = load_module()

    def test_parse_pr_url(self):
        ref = self.review.parse_pr_url("https://github.com/example/project/pull/123")
        self.assertEqual(ref.owner, "example")
        self.assertEqual(ref.repo, "project")
        self.assertEqual(ref.number, 123)

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            self.review.parse_pr_url("https://github.com/example/project/issues/123")

    def test_render_review_contains_required_sections(self):
        data = self.review.ReviewData(
            title="Add billing workflow",
            author="octocat",
            url="https://github.com/example/project/pull/123",
            files=[
                self.review.ChangedFile(
                    filename=".github/workflows/deploy.yml",
                    status="modified",
                    additions=20,
                    deletions=5,
                ),
                self.review.ChangedFile(
                    filename="src/auth/billing.ts",
                    status="modified",
                    additions=140,
                    deletions=40,
                ),
                self.review.ChangedFile(
                    filename="README.md",
                    status="modified",
                    additions=10,
                    deletions=1,
                ),
            ],
        )
        output = self.review.render_review(data)
        self.assertIn("## Summary of Changes", output)
        self.assertIn("## Identified Risks", output)
        self.assertIn("## Improvement Suggestions", output)
        self.assertIn("## Confidence Score", output)
        self.assertIn("No obvious test files changed", output)
        self.assertIn("Sensitive paths changed", output)
        self.assertRegex(output, r"Confidence is (Low|Medium|High)")

    def test_high_confidence_for_small_tested_pr(self):
        data = self.review.ReviewData(
            title="Fix parser",
            author="octocat",
            url="https://github.com/example/project/pull/124",
            files=[
                self.review.ChangedFile("src/parser.py", "modified", 20, 4),
                self.review.ChangedFile("tests/test_parser.py", "modified", 30, 1),
            ],
        )
        risks = self.review.build_risks(data)
        self.assertEqual(self.review.confidence(data, risks), "High")


if __name__ == "__main__":
    unittest.main()
