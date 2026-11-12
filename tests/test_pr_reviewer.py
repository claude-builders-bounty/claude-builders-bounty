#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Claude Code PR Reviewer Sub-Agent
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents", "pr-reviewer"))
from claude_review import parse_pr_url, analyze_diff, format_markdown_review


class TestPRReviewer(unittest.TestCase):

    # 1. URL Parsing Tests
    def test_parse_pr_url_standard(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/onyx-dot-app/onyx/pull/17689")
        self.assertEqual(owner, "onyx-dot-app")
        self.assertEqual(repo, "onyx")
        self.assertEqual(pr_num, 17689)

    def test_parse_pr_url_trailing_slash(self):
        owner, repo, pr_num = parse_pr_url("https://github.com/facebook/react/pull/42/")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(pr_num, 42)

    def test_parse_pr_url_shorthand(self):
        owner, repo, pr_num = parse_pr_url("owner/my-project#105")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "my-project")
        self.assertEqual(pr_num, 105)

    def test_parse_pr_url_invalid(self):
        invalid_urls = [
            "https://google.com",
            "not_a_url",
            "https://github.com/owner/repo/issues/12",
        ]
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                parse_pr_url(url)

    # 2. Risk Detection Tests
    def test_eval_code_execution_detection(self):
        pr_meta = {"title": "Dynamic Parser", "changed_files": 1, "additions": 10, "deletions": 2}
        diff = "+ def parse(expr):\n+     return eval(expr)\n"
        analysis = analyze_diff(pr_meta, diff)
        self.assertTrue(any("eval()" in r for r in analysis["risks"]))

    def test_shell_injection_detection(self):
        pr_meta = {"title": "Shell Runner", "changed_files": 1, "additions": 15, "deletions": 0}
        diff = "+ import subprocess\n+ subprocess.Popen(cmd, shell=True)\n"
        analysis = analyze_diff(pr_meta, diff)
        self.assertTrue(any("shell=True" in r for r in analysis["risks"]))

    def test_hardcoded_secret_detection(self):
        pr_meta = {"title": "Add Auth Client", "changed_files": 1, "additions": 5, "deletions": 1}
        diff = "+ API_KEY = 'dummy_secret_token_placeholder_12345'\n"
        analysis = analyze_diff(pr_meta, diff)
        self.assertTrue(any("secret" in r.lower() or "credential" in r.lower() for r in analysis["risks"]))

    def test_sql_injection_detection(self):
        pr_meta = {"title": "User Query", "changed_files": 1, "additions": 8, "deletions": 2}
        diff = "+ query = 'SELECT * FROM users WHERE name = ' + user_input + ';'\n"
        analysis = analyze_diff(pr_meta, diff)
        self.assertTrue(any("sql" in r.lower() for r in analysis["risks"]))

    def test_exception_swallowing_detection(self):
        pr_meta = {"title": "Ignore Errors", "changed_files": 1, "additions": 12, "deletions": 4}
        diff = "+ try:\n+     do_work()\n+ except:\n+     pass\n"
        analysis = analyze_diff(pr_meta, diff)
        self.assertTrue(any("swallowing" in r.lower() or "except: pass" in r for r in analysis["risks"]))

    def test_large_addition_without_tests(self):
        pr_meta = {"title": "Big Feature", "changed_files": 8, "additions": 350, "deletions": 20}
        diff = "+ # Large implementation without any test files\n" * 20
        analysis = analyze_diff(pr_meta, diff)
        self.assertTrue(any("test coverage" in r.lower() for r in analysis["risks"]))

    # 3. Clean Diff & Confidence Scoring Tests
    def test_clean_diff_high_confidence(self):
        pr_meta = {"title": "Fix Typo and Update Tests", "changed_files": 2, "additions": 25, "deletions": 5}
        diff = "+ # Clean bug fix\n+ def test_fix():\n+     assert True\n"
        analysis = analyze_diff(pr_meta, diff)
        self.assertEqual(analysis["confidence"], "High")
        self.assertIn("No critical", analysis["risks"][0])

    def test_format_markdown_adherence(self):
        analysis = {
            "title": "Sample Feature",
            "files_changed": 3,
            "additions": 45,
            "deletions": 10,
            "summary": "This pull request modifies 3 files. Focuses on Feature. Overall high confidence.",
            "risks": ["No critical security vulnerabilities or severe anti-patterns detected."],
            "suggestions": ["Verify CI build passes cleanly."],
            "confidence": "High",
        }
        md = format_markdown_review(analysis)
        self.assertIn("## 🤖 Claude Code PR Review", md)
        self.assertIn("### Summary", md)
        self.assertIn("### Identified Risks", md)
        self.assertIn("### Improvement Suggestions", md)
        self.assertIn("### Confidence Score", md)
        self.assertIn("**High**", md)


if __name__ == "__main__":
    unittest.main()
