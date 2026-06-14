import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "claude-review"
AGENT = ROOT / ".claude" / "agents" / "pr-reviewer.md"
MODULE = runpy.run_path(str(CLI))

parse_pr_url = MODULE["parse_pr_url"]
canonical_pr_url = MODULE["canonical_pr_url"]
parse_diff = MODULE["parse_diff"]
identify_risks = MODULE["identify_risks"]
render_markdown = MODULE["render_markdown"]

SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,3 @@
+API_TOKEN = "example"
+def export_data():
 print("ok")
"""


class ClaudeReviewTest(unittest.TestCase):
    def test_canonical_agent_manifest(self):
        agent = AGENT.read_text(encoding="utf-8")
        self.assertIn("name: pr-reviewer", agent)
        self.assertIn("tools: Bash, Read, Grep", agent)
        self.assertIn("### Confidence score", agent)

    def test_accepts_pr_url_suffix_and_canonicalizes_it(self):
        parts = parse_pr_url("https://github.com/owner/repo/pull/123/files?tab=files")
        self.assertEqual(parts, ("owner", "repo", "123"))
        self.assertEqual(canonical_pr_url(*parts), "https://github.com/owner/repo/pull/123")

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/owner/repo/issues/123")

    def test_parses_file_stats(self):
        files = parse_diff(SAMPLE_DIFF)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].path, "app.py")
        self.assertEqual(files[0].additions, 2)
        self.assertEqual(files[0].hunks, 1)

    def test_detects_sensitive_configuration(self):
        files = parse_diff(SAMPLE_DIFF)
        risks = identify_risks(files, SAMPLE_DIFF)
        self.assertTrue(any("credential-like literal" in risk for risk in risks))

    def test_renders_all_required_sections(self):
        files = parse_diff(SAMPLE_DIFF)
        output = render_markdown(
            "https://github.com/owner/repo/pull/123",
            {"title": "Export data"},
            files,
            SAMPLE_DIFF,
        )
        for heading in (
            "### Summary of changes",
            "### Identified risks",
            "### Improvement suggestions",
            "### Changed files",
            "### Confidence score",
        ):
            self.assertIn(heading, output)

    def test_cli_reviews_local_diff_without_network(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_path = Path(temp_dir) / "change.diff"
            diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--pr",
                    "https://github.com/owner/repo/pull/123/files",
                    "--diff-file",
                    str(diff_path),
                    "--title",
                    "Offline fixture",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"Offline fixture"', result.stdout)
        self.assertIn("Source: https://github.com/owner/repo/pull/123", result.stdout)


if __name__ == "__main__":
    unittest.main()
