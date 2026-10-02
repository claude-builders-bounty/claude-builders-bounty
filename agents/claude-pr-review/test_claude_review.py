import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from claude_review import parse_pr_url, analyze_diff, main

class TestClaudePRReviewAgent(unittest.TestCase):
    def test_parse_pr_url_valid(self):
        url = "https://github.com/owner/repo/pull/123"
        owner, repo, pr_id = parse_pr_url(url)
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(pr_id, "123")

    def test_parse_pr_url_invalid(self):
        url = "https://github.com/owner/repo/issues/123"
        with self.assertRaises(ValueError):
            parse_pr_url(url)

    def test_analyze_diff_empty(self):
        result = analyze_diff("", "testowner", "testrepo", "1")
        self.assertIn("Empty PR or no diff changes detected", result)
        self.assertIn("Confidence Score: **High**", result)

    def test_analyze_diff_structured_markdown(self):
        mock_diff = """diff --git a/src/index.js b/src/index.js
index 0000000..1111111 100644
--- a/src/index.js
+++ b/src/index.js
@@ -0,0 +1,5 @@
+console.log("hello world");
+const token = "abc";
+eval("alert(1)");
"""
        result = analyze_diff(mock_diff, "testowner", "testrepo", "42")
        # Check required sections
        self.assertIn("### 📋 Summary of Changes", result)
        self.assertIn("### ⚠️ Identified Risks & Blast Radius", result)
        self.assertIn("### 💡 Improvement Suggestions", result)
        self.assertIn("Confidence Score:", result)
        self.assertTrue("Low" in result or "Medium" in result or "High" in result)
        # Check heuristics triggered
        self.assertIn("Potential hardcoded credential or dynamic code execution pattern detected", result)
        self.assertIn("No explicit test files found", result)

    def test_analyze_diff_with_tests(self):
        mock_diff = """diff --git a/test/index.test.js b/test/index.test.js
index 0000000..1111111 100644
--- a/test/index.test.js
+++ b/test/index.test.js
@@ -0,0 +1,10 @@
+test("works", () => {});
"""
        result = analyze_diff(mock_diff, "testowner", "testrepo", "100")
        self.assertIn("Confidence Score: **High**", result)
        self.assertIn("✅ Included", result)

    @patch("argparse.ArgumentParser.parse_args")
    def test_cli_parsing_diff_file(self, mock_parse_args):
        # Create temp diff
        diff_file = "/tmp/test_diff.patch"
        with open(diff_file, "w") as f:
            f.write("diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@ -0,0 +1 @@\n+test\n")

        mock_parse_args.return_value = MagicMock(
            pr=None,
            diff_file=diff_file,
            post_comment=False,
            output=None
        )

        with patch("sys.stdout") as mock_stdout:
            main()
        
        if os.path.exists(diff_file):
            os.remove(diff_file)

if __name__ == "__main__":
    unittest.main()
