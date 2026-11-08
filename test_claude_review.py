import unittest
from claude_review import parse_pr_url, analyze_diff, format_review_markdown

class TestClaudeReview(unittest.TestCase):
    def test_parse_pr_url_valid(self):
        url = "https://github.com/owner/repo/pull/123"
        owner, repo, num = parse_pr_url(url)
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(num, 123)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/not-a-pr")

    def test_analyze_diff_risk_detection(self):
        meta = {
            "title": "Add secrets",
            "body": "Fixing token",
            "files": [{"path": "config.yaml"}]
        }
        diff = "+ api_key = 'supersecret'\n- old_key = '123'"
        analysis = analyze_diff(meta, diff)
        self.assertIn("Dependency or CI configuration modifications detected", analysis["risks"][0])
        self.assertTrue(any("sensitive" in r for r in analysis["risks"]))

    def test_format_review_markdown(self):
        analysis = {
            "summary": "Test summary.",
            "risks": ["Risk 1"],
            "suggestions": ["Suggestion 1"],
            "confidence": "High",
            "files_count": 1,
            "additions": 10,
            "deletions": 2
        }
        md = format_review_markdown(analysis)
        self.assertIn("## 🤖 Automated PR Review", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("Risk 1", md)
        self.assertIn("Confidence Score: **High**", md)

if __name__ == "__main__":
    unittest.main()
