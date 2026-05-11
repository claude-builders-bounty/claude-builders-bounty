import unittest
from unittest.mock import patch
from tools.claude_review import analyze_diff

class TestClaudeReview(unittest.TestCase):
    def test_analyze_small_diff(self):
        diff = """diff --git a/test.txt b/test.txt
+print("hello")
-func()
"""
        r = analyze_diff(diff)
        self.assertEqual(r["files"], 1)
        self.assertEqual(r["added"], 1)
        self.assertEqual(r["removed"], 1)
        self.assertEqual(r["confidence"], "Low")

    def test_analyze_large_diff(self):
        diff = "diff --git a/test.txt b/test.txt\n" + "\n".join(f"+line_{i}" for i in range(200))
        r = analyze_diff(diff)
        self.assertEqual(r["confidence"], "High")
        self.assertTrue(len(r["suggestions"]) > 0)

if __name__ == "__main__":
    unittest.main()