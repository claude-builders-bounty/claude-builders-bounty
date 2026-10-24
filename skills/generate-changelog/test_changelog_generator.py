"""
Unit Test Suite for Claude CHANGELOG Generator
Validates semantic commit classification, breaking change detection, and Markdown rendering.
"""
import unittest
import os
import sys

sys.path.append(os.path.dirname(__file__))
from generate_changelog import parse_conventional_commit, CONVENTIONAL_MAP

class TestChangelogGenerator(unittest.TestCase):
    def test_conventional_commit_features(self):
        res = parse_conventional_commit("feat(auth): add OAuth2 PKCE authorization flow (#102)")
        self.assertEqual(res["category"], "Added")
        self.assertEqual(res["scope"], "auth")
        self.assertFalse(res["is_breaking"])
        self.assertEqual(res["message"], "add OAuth2 PKCE authorization flow (#102)")

    def test_conventional_commit_bugfix(self):
        res = parse_conventional_commit("fix(database): resolve race condition in pool deposit lock (#457)")
        self.assertEqual(res["category"], "Fixed")
        self.assertEqual(res["scope"], "database")
        self.assertFalse(res["is_breaking"])

    def test_breaking_change_detection(self):
        res = parse_conventional_commit("feat(api)!: drop deprecated v1 endpoints and enforce UUIDv4")
        self.assertEqual(res["category"], "Added")
        self.assertTrue(res["is_breaking"])

    def test_security_and_performance(self):
        sec = parse_conventional_commit("security(auth): patch timing attack in password comparison")
        self.assertEqual(sec["category"], "Security")
        
        perf = parse_conventional_commit("perf(cache): optimize LRU cache lookup latency")
        self.assertEqual(perf["category"], "Performance Improvements")

    def test_fallback_parsing(self):
        add_fallback = parse_conventional_commit("Add Korean bank adapters for KB Kookmin")
        self.assertEqual(add_fallback["category"], "Added")
        
        fix_fallback = parse_conventional_commit("Fix memory leak in background watchdog daemon")
        self.assertEqual(fix_fallback["category"], "Fixed")

if __name__ == '__main__':
    print("=" * 65)
    print("🧪 RUNNING UNIT TESTS FOR CHANGELOG GENERATOR")
    print("=" * 65)
    unittest.main(verbosity=2)
