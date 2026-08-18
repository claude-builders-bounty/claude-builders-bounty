import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from claude_review import analyze_diff, format_markdown_review

class TestClaudePRReviewer(unittest.TestCase):
    def setUp(self):
        self.sample_diff = """--- a/src/app.py
+++ b/src/app.py
@@ -10,6 +10,8 @@ def authenticate(user, password):
-    db.query("SELECT * FROM users")
+    secret_token = "sk_live_1234567890abcdef"
+    eval(user_input)
+    rm -rf /tmp/data
"""

    def test_detects_hardcoded_credentials(self):
        analysis = analyze_diff(self.sample_diff)
        risks = "\n".join(analysis["risks"])
        self.assertIn("Hardcoded Credential Warning", risks)

    def test_detects_command_injection(self):
        analysis = analyze_diff(self.sample_diff)
        risks = "\n".join(analysis["risks"])
        self.assertIn("Command Injection Risk", risks)

    def test_detects_destructive_commands(self):
        analysis = analyze_diff(self.sample_diff)
        risks = "\n".join(analysis["risks"])
        self.assertIn("Destructive Command Risk", risks)

    def test_formats_markdown_correctly(self):
        analysis = analyze_diff(self.sample_diff)
        md = format_markdown_review(analysis, "test_diff.patch")
        self.assertIn("# 🤖 Claude PR Review Report", md)
        self.assertIn("Confidence Score", md)

if __name__ == "__main__":
    unittest.main()
