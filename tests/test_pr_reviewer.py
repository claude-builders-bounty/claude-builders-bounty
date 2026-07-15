#!/usr/bin/env python3
"""
Tests for pr_reviewer.py
Bounty: claude-builders-bounty/claude-builders-bounty #4
"""

import unittest
import sys
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent / 'pr-reviewer'))
from pr_reviewer import PRReviewer, ReviewSeverity, ReviewCategory, ReviewFinding


class TestPRReviewer(unittest.TestCase):
    """Test cases for pr_reviewer.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.reviewer = PRReviewer()

    def test_check_security_hardcoded_password(self):
        """Test detection of hardcoded password"""
        code = 'password = "secret123"'
        findings = self.reviewer._check_security(code, "test.py", 1)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, ReviewSeverity.CRITICAL)
        self.assertEqual(findings[0].category, ReviewCategory.SECURITY)

    def test_check_security_hardcoded_api_key(self):
        """Test detection of hardcoded API key"""
        code = 'api_key = "sk-abc123"'
        findings = self.reviewer._check_security(code, "test.py", 1)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, ReviewSeverity.CRITICAL)

    def test_check_security_sql_injection(self):
        """Test detection of SQL injection risk"""
        code = 'db.execute("SELECT * FROM users WHERE id = " + user_id)'
        findings = self.reviewer._check_security(code, "test.py", 1)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, ReviewSeverity.HIGH)

    def test_check_bug_risk_todo(self):
        """Test detection of TODO without issue ref"""
        code = '# TODO: fix this later'
        findings = self.reviewer._check_bug_risk(code, "test.py", 1)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, ReviewCategory.BUG)

    def test_check_style_long_line(self):
        """Test detection of long lines"""
        code = 'x = "' + 'a' * 130 + '"'
        findings = self.reviewer._check_style(code, "test.py", 1)

        self.assertEqual(len(findings), 1)
        self.assertIn("too long", findings[0].message.lower())

    def test_parse_diff_files(self):
        """Test diff parsing"""
        diff = '''diff --git a/file1.py b/file1.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file1.py
@@ -0,0 +1 @@
+print("hello")
'''
        files = self.reviewer.parse_diff_files(diff)
        self.assertIn("file1.py", files)


if __name__ == '__main__':
    unittest.main()
