import unittest
from agents.claude_review import parse_pr_url, analyze_diff, format_markdown_review

class TestClaudeReview(unittest.TestCase):
    def test_parse_pr_url_valid(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/owner/my-repo/pull/42")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "my-repo")
        self.assertEqual(pr_num, 42)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://example.com/invalid")

    def test_analyze_diff_detection(self):
        pr_data = {"title": "Test PR", "changed_files": 2, "additions": 40, "deletions": 5}
        diff_text = "+ eval(userInput);"
        res = analyze_diff(pr_data, diff_text)
        self.assertIn("Potential arbitrary code execution", res["risks"][0])

    def test_format_markdown_structure(self):
        analysis = {
            "summary": "Sample summary text.",
            "risks": ["Risk 1"],
            "suggestions": ["Suggestion 1"],
            "confidence": "High"
        }
        md = format_markdown_review(analysis)
        self.assertIn("## 🤖 Claude Code Review Summary", md)
        self.assertIn("### ⚠️ Identified Risks", md)
        self.assertIn("### 💡 Improvement Suggestions", md)
        self.assertIn("**Confidence Score:** `High`", md)

if __name__ == "__main__":
    unittest.main()
