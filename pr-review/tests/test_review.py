import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_review import analyze_diff

class TestClaudeReview(unittest.TestCase):
    def test_analyze_diff_security(self):
        diff = "+++ b/file.py\n+password = 'secret'\n+eval(user_input)\n"
        result = analyze_diff(diff)
        combined_risks = " ".join(result['risks'])
        self.assertIn("Potential hardcoded credential found", combined_risks)
        self.assertIn("eval()", combined_risks)
        self.assertEqual(result['confidence'], 'High')

    def test_analyze_diff_improvements(self):
        diff = "+++ b/file.py\n+try:\n+    pass\n+except:\n+    pass\n"
        result = analyze_diff(diff)
        combined_improvements = " ".join(result['improvements'])
        self.assertIn("Bare 'except:' block found", combined_improvements)
        
    def test_clean_code(self):
        diff = "+++ b/file.py\n+def hello():\n+    print('Hello World')\n"
        result = analyze_diff(diff)
        self.assertEqual(result['confidence'], 'Low')
        self.assertIn("No critical security risks", result['risks'][0])

if __name__ == '__main__':
    unittest.main()
