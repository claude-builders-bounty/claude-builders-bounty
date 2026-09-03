import unittest
from claude_review import parse_pr_url, analyze_diff, format_review_markdown

class TestClaudeReviewAgent(unittest.TestCase):

    def test_parse_valid_pr_urls(self):
        urls = [
            ("https://github.com/facebook/react/pull/12345", ("facebook", "react", 12345)),
            ("https://github.com/vercel/next.js/pull/999", ("vercel", "next.js", 999)),
            ("github.com/owner/repo/pull/42", ("owner", "repo", 42))
        ]
        for url, expected in urls:
            with self.subTest(url=url):
                self.assertEqual(parse_pr_url(url), expected)

    def test_parse_invalid_urls(self):
        invalid_urls = [
            "https://github.com/owner/repo/issues/123",
            "https://google.com",
            "https://github.com/owner/repo"
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    parse_pr_url(url)

    def test_secret_detection_and_low_confidence(self):
        meta = {"title": "Update config", "additions": 10, "deletions": 2}
        files = [
            {
                "filename": "config.py",
                "patch": "@@ -1,3 +1,4 @@\n+GITHUB_TOKEN = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'"
            }
        ]
        res = analyze_diff(meta, files)
        self.assertEqual(res["confidence"], "Low")
        self.assertTrue(any("Security: Possible raw GitHub token committed" in r for r in res["risks"]))

    def test_destructive_command_detection(self):
        meta = {"title": "Cleanup script", "additions": 5, "deletions": 0}
        files = [
            {
                "filename": "deploy.sh",
                "patch": "@@ -0,0 +1,5 @@\n+rm -rf /tmp/cache\n+git push origin main --force"
            }
        ]
        res = analyze_diff(meta, files)
        self.assertTrue(any("rm -rf" in r for r in res["risks"]))
        self.assertTrue(any("Forced push" in r for r in res["risks"]))

    def test_high_confidence_clean_pr_with_tests(self):
        meta = {"title": "feat: add user profile card", "additions": 50, "deletions": 5}
        files = [
            {
                "filename": "src/components/user-card.tsx",
                "patch": "@@ -0,0 +1,50 @@\n+export function UserCard() {}"
            },
            {
                "filename": "src/components/user-card.test.tsx",
                "patch": "@@ -0,0 +1,30 @@\n+describe('UserCard', () => {})"
            }
        ]
        res = analyze_diff(meta, files)
        self.assertEqual(res["confidence"], "High")
        self.assertFalse(any("Security:" in r for r in res["risks"]))

    def test_markdown_output_structure(self):
        analysis = {
            "summary": "This PR updates authentication middleware and adds integration tests.",
            "risks": ["Database migration requires downtime check."],
            "suggestions": ["Add rollback plan."],
            "confidence": "Medium"
        }
        md = format_review_markdown(analysis)
        self.assertIn("## Summary of Changes", md)
        self.assertIn("## Identified Risks", md)
        self.assertIn("## Improvement Suggestions", md)
        self.assertIn("## Confidence Score", md)
        self.assertIn("**Medium**", md)


if __name__ == "__main__":
    unittest.main()
