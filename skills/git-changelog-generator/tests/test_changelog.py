#!/usr/bin/env python3
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from generate_changelog import categorize_commit

class TestGitChangelog(unittest.TestCase):

    def test_conventional_feat(self):
        cat, msg = categorize_commit("feat(auth): implement oauth2 token rotation")
        self.assertEqual(cat, "Added")
        self.assertEqual(msg, "implement oauth2 token rotation")

    def test_conventional_fix(self):
        cat, msg = categorize_commit("fix: resolve null pointer exception in parser")
        self.assertEqual(cat, "Fixed")
        self.assertEqual(msg, "resolve null pointer exception in parser")

    def test_conventional_docs(self):
        cat, msg = categorize_commit("docs: add 3-step setup guide")
        self.assertEqual(cat, "Documentation")
        self.assertEqual(msg, "add 3-step setup guide")

    def test_conventional_security(self):
        cat, msg = categorize_commit("security: sanitize shell inputs")
        self.assertEqual(cat, "Security")
        self.assertEqual(msg, "sanitize shell inputs")

    def test_conventional_refactor(self):
        cat, msg = categorize_commit("refactor(core): streamline category mapping")
        self.assertEqual(cat, "Changed")
        self.assertEqual(msg, "streamline category mapping")

    def test_fallback_keywords(self):
        cat, msg = categorize_commit("Add new test cases for validator")
        self.assertEqual(cat, "Added")
        
        cat, msg = categorize_commit("Patch memory leak in cache layer")
        self.assertEqual(cat, "Fixed")

if __name__ == '__main__':
    unittest.main()
