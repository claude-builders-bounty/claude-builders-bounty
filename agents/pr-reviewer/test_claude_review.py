import unittest
from claude_review import parse_pr_url, analyze_diff, generate_structured_review


class TestPRReviewerAgent(unittest.TestCase):
    def test_parse_pr_url(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/facebook/react/pull/42")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(pr_num, 42)

    def test_parse_pr_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/facebook/react/issues/42")

    def test_analyze_diff_detects_credentials(self):
        diff = '+ const apiKey = "AIzaSyD-secret-token-key-123456";\n'
        analysis = analyze_diff(diff, "Add API client", "", 1, 0)
        self.assertTrue(any("secret" in r or "token" in r for r in analysis["risks"]))
        self.assertIn(analysis["confidence"], ["Medium", "Low"])

    def test_generate_structured_review_format(self):
        mock_metadata = {
            "title": "feat: add user authentication",
            "body": "Implements login and registration.",
            "additions": 45,
            "deletions": 10,
            "changedFiles": 3,
            "diff": "+ function login() { return true; }",
            "author": {"login": "octocat"},
        }
        review = generate_structured_review(mock_metadata)
        self.assertIn("## 🤖 Claude Code PR Review", review)
        self.assertIn("### 📝 Summary of Changes", review)
        self.assertIn("### ⚠️ Identified Risks", review)
        self.assertIn("### 💡 Improvement Suggestions", review)
        self.assertIn("### 🎯 Confidence Score:", review)


if __name__ == "__main__":
    unittest.main()
