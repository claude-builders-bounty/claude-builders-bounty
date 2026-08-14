import importlib.util
import sys
import unittest
from pathlib import Path


_MODULE_PATH = Path(__file__).parents[1] / "claude-review" / "review.py"
_SPEC = importlib.util.spec_from_file_location("claude_review_review", _MODULE_PATH)
assert _SPEC and _SPEC.loader
review = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = review
_SPEC.loader.exec_module(review)


class ReviewTests(unittest.TestCase):
    def test_parse_public_pr_url(self):
        self.assertEqual(
            review.parse_pr_url("https://github.com/owner/project/pull/42"),
            ("owner", "project", 42),
        )

    def test_rejects_non_github_url(self):
        with self.assertRaises(ValueError):
            review.parse_pr_url("https://example.com/owner/project/pull/42")

    def test_render_contains_required_sections(self):
        pr = review.PullRequest(
            owner="owner",
            repo="project",
            number=42,
            title="Add feature",
            body="",
            changed_files=1,
            additions=3,
            deletions=0,
            mergeable=True,
        )
        output = review.render_review(
            pr,
            [{"filename": "src/auth.py", "patch": "+ subprocess.run(user_input)\n", "status": "modified"}],
        )
        for heading in (
            "## Summary",
            "## Identified risks",
            "## Improvement suggestions",
            "## Confidence",
        ):
            self.assertIn(heading, output)
        self.assertIn("High", output)


if __name__ == "__main__":
    unittest.main()
