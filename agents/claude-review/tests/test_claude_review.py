#!/usr/bin/env python3
"""
Automated unit tests for claude_review.py.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_review import parse_pr_url, analyze_diff, format_review_markdown

class TestClaudeReviewAgent(unittest.TestCase):
    def test_parse_pr_url(self):
        owner, repo, num = parse_pr_url("https://github.com/anthropic/claude-code/pull/999")
        self.assertEqual(owner, "anthropic")
        self.assertEqual(repo, "claude-code")
        self.assertEqual(num, 999)

    def test_parse_invalid_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://google.com/invalid")

    def test_analyze_diff_safe(self):
        pr_meta = {
            "title": "feat: add user profile page",
            "body": "Implements user profile UI with unit tests.",
            "changed_files": 2,
            "additions": 45,
            "deletions": 5,
        }
        diff = """diff --git a/src/profile.ts b/src/profile.ts
+export function getProfile() { return 'profile'; }
diff --git a/tests/profile.test.ts b/tests/profile.test.ts
+test('profile', () => expect(getProfile()).toBe('profile'));
"""
        analysis = analyze_diff(pr_meta, diff)
        self.assertEqual(analysis["confidence"], "High")
        self.assertEqual(len(analysis["risks"]), 0)
        
        md = format_review_markdown(analysis)
        self.assertIn("## 🤖 Claude PR Review", md)
        self.assertIn("### 📝 Summary of Changes", md)
        self.assertIn("🟢 **High**", md)

    def test_analyze_diff_destructive_and_secret(self):
        pr_meta = {
            "title": "fix: cleanup script",
            "body": "quick fix",
            "changed_files": 1,
            "additions": 10,
            "deletions": 0,
        }
        diff = """diff --git a/scripts/clean.sh b/scripts/clean.sh
+TOKEN="ghp_123456789012345678901234567890123456"
+rm -rf /tmp/data
"""
        analysis = analyze_diff(pr_meta, diff)
        self.assertEqual(analysis["confidence"], "Low")
        self.assertTrue(any("Security Warning" in r for r in analysis["risks"]))
        self.assertTrue(any("Destructive Operation" in r for r in analysis["risks"]))

if __name__ == "__main__":
    unittest.main()
