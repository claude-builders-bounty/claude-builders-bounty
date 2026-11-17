import unittest
from claude_review import analyze_diff_heuristics, format_markdown_review, parse_pr_url


class TestClaudeReviewSubagent(unittest.TestCase):
    def test_parse_pr_url_valid(self):
        owner, repo, num = parse_pr_url("https://github.com/overturn-ai/overturn/pull/54")
        self.assertEqual(owner, "overturn-ai")
        self.assertEqual(repo, "overturn")
        self.assertEqual(num, 54)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/overturn-ai/overturn/issues/22")

    def test_analyze_diff_with_tests_high_confidence(self):
        sample_diff = """diff --git a/src/capture.ts b/src/capture.ts
+++ b/src/capture.ts
+export function capture() { return true; }
diff --git a/src/capture.test.ts b/src/capture.test.ts
+++ b/src/capture.test.ts
+test('capture works', () => { expect(capture()).toBe(true); });
"""
        meta = {"title": "feat(gorgias-app): add capture adapter", "additions": 25, "deletions": 0, "changed_files": 2}
        res = analyze_diff_heuristics(meta, sample_diff)
        self.assertEqual(res["confidence"], "High")
        self.assertIn("2 file(s)", res["summary"])
        md = format_markdown_review(res, "https://github.com/overturn-ai/overturn/pull/54")
        self.assertIn("### 📋 Summary of Changes", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("### 🎯 Confidence Score\n**High**", md)

    def test_analyze_diff_without_tests_flags_risk(self):
        sample_diff = """diff --git a/src/main.py b/src/main.py
+++ b/src/main.py
+# TODO: fix later
+def run(): pass
"""
        meta = {"title": "feat: add main runner", "additions": 10, "deletions": 2, "changed_files": 1}
        res = analyze_diff_heuristics(meta, sample_diff)
        self.assertTrue(any("No test files" in r for r in res["risks"]))
        self.assertTrue(any("TODO" in s for s in res["suggestions"]))


if __name__ == "__main__":
    unittest.main()
