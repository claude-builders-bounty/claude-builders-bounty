import unittest
from claude_review import analyze_diff, format_markdown_review

class TestReviewer(unittest.TestCase):
    def test_clean_diff_analysis(self):
        sample_diff = """diff --git a/src/math.ts b/src/math.ts
--- a/src/math.ts
+++ b/src/math.ts
@@ -1,3 +1,4 @@
+export function add(a: number, b: number): number {
+  return a + b;
+}
"""
        analysis = analyze_diff(sample_diff)
        self.assertEqual(analysis["confidence"], "High")
        self.assertEqual(analysis["file_count"], 1)
        self.assertEqual(analysis["add_count"], 3)
        self.assertIn("No critical security hazards", analysis["risks"][0])

    def test_secret_detection(self):
        sample_diff = """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
+API_KEY = "sk_live_123456789abcdef"
"""
        analysis = analyze_diff(sample_diff)
        self.assertEqual(analysis["confidence"], "Low")
        self.assertTrue(any("secret" in r.lower() for r in analysis["risks"]))

if __name__ == '__main__':
    unittest.main()
