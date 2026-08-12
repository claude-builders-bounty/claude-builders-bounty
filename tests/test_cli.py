import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "claude-review"


class ReviewCliTest(unittest.TestCase):
    def run_cli(self, args, gh_text, claude_text):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "gh").write_text(
                "#!/bin/sh\nprintf '%s' \"$GH_DIFF\"\n", encoding="utf-8"
            )
            (directory / "claude").write_text(
                "#!/bin/sh\ncat >\"$PROMPT_PATH\"\nprintf '%s' \"$CLAUDE_REVIEW\"\n",
                encoding="utf-8",
            )
            os.chmod(directory / "gh", 0o755)
            os.chmod(directory / "claude", 0o755)
            env = os.environ | {
                "PATH": f"{directory}:{os.environ['PATH']}",
                "GH_DIFF": gh_text,
                "CLAUDE_REVIEW": claude_text,
                "PROMPT_PATH": str(directory / "prompt.txt"),
            }
            result = subprocess.run(
                ["python3", str(SCRIPT), *args],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.last_prompt = (directory / "prompt.txt").read_text(encoding="utf-8")
            return result

    def test_pr_url_fetches_patch_and_preserves_required_sections(self):
        review = (
            "## Summary\nA change.\n\n"
            "## Identified Risks\n- A risk.\n\n"
            "## Improvement Suggestions\n- Add a test.\n\n"
            "## Confidence\nMedium\n"
        )
        result = self.run_cli(
            ["--pr", "https://github.com/example/project/pull/1"],
            "diff --git a/app.py b/app.py\n+return 1\n",
            review,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, review)

    def test_prompt_does_not_contain_patch_markers(self):
        result = self.run_cli(
            ["--pr", "https://github.com/example/project/pull/1"],
            "diff --git a/app.py b/app.py\n+return 1\n",
            "## Summary\nA.\n\n## Identified Risks\n- None.\n\n"
            "## Improvement Suggestions\n- None.\n\n## Confidence\nHigh\n",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("+        Review this GitHub", self.last_prompt)
        self.assertIn("Review this GitHub pull request", self.last_prompt)

    def test_missing_sections_get_safe_fallback(self):
        result = self.run_cli(
            ["--diff-file", str(ROOT / "README.md")],
            "diff --git a/README.md b/README.md\n",
            "Only a summary.",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Identified Risks", result.stdout)
        self.assertIn("## Confidence\nLow", result.stdout)


if __name__ == "__main__":
    unittest.main()
