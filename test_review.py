import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claude_review import analyze_diff

class TestPRReviewer(unittest.TestCase):
    def test_clean_diff_review(self):
        sample_diff = """diff --git a/src/math.ts b/src/math.ts
index 1234567..89abcdef 100644
--- a/src/math.ts
+++ b/src/math.ts
@@ -1,2 +1,4 @@
 export function add(a: number, b: number): number {
+    return a + b;
 }
"""
        review = analyze_diff(sample_diff)
        self.assertIn("## 🔍 Claude Code PR Review", review)
        self.assertIn("### 📝 Summary of Changes", review)
        self.assertIn("### ⚠️ Identified Risks & Potential Issues", review)
        self.assertIn("### 💡 Improvement Suggestions", review)
        self.assertIn("### 🎯 Confidence Score", review)

    def test_detects_unsafe_eval(self):
        unsafe_diff = """diff --git a/src/calc.ts b/src/calc.ts
--- a/src/calc.ts
+++ b/src/calc.ts
@@ -1,1 +1,2 @@
+const res = eval(userInput);
"""
        review = analyze_diff(unsafe_diff)
        self.assertIn("Dynamic code execution (`eval`/`exec`) detected", review)
        self.assertIn("Confidence:", review)

if __name__ == "__main__":
    unittest.main()
