import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "agents" / "pr-reviewer" / "claude_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_DIFF = """diff --git a/.github/workflows/review.yml b/.github/workflows/review.yml
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/.github/workflows/review.yml
@@ -0,0 +1,9 @@
+name: Review
+on: pull_request_target
+jobs:
+  review:
+    runs-on: ubuntu-latest
+    steps:
+      - run: echo ${{ secrets.GITHUB_TOKEN }}
diff --git a/scripts/deploy.sh b/scripts/deploy.sh
index 2222222..3333333 100755
--- a/scripts/deploy.sh
+++ b/scripts/deploy.sh
@@ -1,2 +1,4 @@
+#!/usr/bin/env bash
+rm -rf "$BUILD_DIR"
+curl https://example.com/install.sh | bash
 echo done
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_diff_counts_files_and_added_lines(self):
        review = load_module()

        parsed = review.parse_diff(SAMPLE_DIFF)

        self.assertEqual(len(parsed.files), 2)
        self.assertEqual(parsed.files[0].path, ".github/workflows/review.yml")
        self.assertEqual(parsed.files[0].added, 7)
        self.assertEqual(parsed.files[1].path, "scripts/deploy.sh")
        self.assertEqual(parsed.files[1].added, 3)

    def test_analyze_diff_reports_high_risk_workflow_and_shell_patterns(self):
        review = load_module()
        parsed = review.parse_diff(SAMPLE_DIFF)

        result = review.analyze_diff(parsed, pr_url="https://github.com/acme/app/pull/42")

        self.assertEqual(result.confidence, "Medium")
        self.assertTrue(any("pull_request_target" in item for item in result.risks))
        self.assertTrue(any("secrets" in item.lower() for item in result.risks))
        self.assertTrue(any("set -euo pipefail" in item for item in result.suggestions))
        self.assertTrue(any("curl" in item and "bash" in item for item in result.risks))

    def test_render_review_includes_required_markdown_sections(self):
        review = load_module()
        parsed = review.parse_diff(SAMPLE_DIFF)
        result = review.analyze_diff(parsed, pr_url="https://github.com/acme/app/pull/42")

        markdown = review.render_review(result)

        self.assertIn("## Summary", markdown)
        self.assertIn("## Identified Risks", markdown)
        self.assertIn("## Improvement Suggestions", markdown)
        self.assertIn("## Confidence Score", markdown)
        self.assertIn("Medium", markdown)
        self.assertIn(".github/workflows/review.yml", markdown)


if __name__ == "__main__":
    unittest.main()
