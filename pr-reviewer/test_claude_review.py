import importlib.machinery
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "claude-review"
loader = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)


class ClaudeReviewTests(unittest.TestCase):
    def test_diff_url_accepts_github_pull_request(self):
        self.assertEqual(
            mod.diff_url("https://github.com/openai/example/pull/123"),
            "https://github.com/openai/example/pull/123.diff",
        )

    def test_diff_url_rejects_non_pull_url(self):
        with self.assertRaises(ValueError):
            mod.diff_url("https://github.com/openai/example/issues/123")

    def test_validate_review_accepts_required_structure(self):
        mod.validate_review(
            "## Summary\nOK\n\n## Identified risks\n- None identified.\n\n"
            "## Improvement suggestions\n- None required.\n\n## Confidence\nHigh"
        )

    def test_validate_review_rejects_bad_confidence(self):
        with self.assertRaises(RuntimeError):
            mod.validate_review(
                "## Summary\nOK\n\n## Identified risks\n- None identified.\n\n"
                "## Improvement suggestions\n- None required.\n\n## Confidence\nCertain"
            )


if __name__ == "__main__":
    unittest.main()
