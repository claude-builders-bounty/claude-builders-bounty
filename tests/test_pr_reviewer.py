import io
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.pr_reviewer import (
    Category,
    DiffParser,
    MarkdownReviewFormatter,
    PRReviewEngine,
    Recommendation,
    ReviewResult,
    Severity,
)

CLEAN_DIFF = """diff --git a/app/calculator.py b/app/calculator.py
new file mode 100644
--- /dev/null
+++ b/app/calculator.py
@@ -0,0 +1,10 @@
+def add(a: int, b: int) -> int:
+    \"\"\"Add two numbers safely.\"\"\"
+    return a + b
diff --git a/tests/test_calculator.py b/tests/test_calculator.py
new file mode 100644
--- /dev/null
+++ b/tests/test_calculator.py
@@ -0,0 +1,8 @@
+import unittest
+from app.calculator import add
+
+class TestCalculator(unittest.TestCase):
+    def test_add(self):
+        self.assertEqual(add(2, 3), 5)
"""

VULNERABLE_DIFF = """diff --git a/app/auth.py b/app/auth.py
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,6 +10,14 @@
+api_key = "mock_secret_api_key_testing_value_987654"
+
+def get_user_data(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    cursor.execute(query)
+    return cursor.fetchall()
+"""

SHELL_AND_PATH_DIFF = """diff --git a/app/utils.py b/app/utils.py
--- a/app/utils.py
+++ b/app/utils.py
@@ -5,6 +5,10 @@
+def run_backup(path):
+    os.system("tar -czf backup.tar.gz " + path)
+    with open(f"/tmp/backups/{path}", "r") as f:
+        return f.read()
"""

QUALITY_ISSUES_DIFF = """diff --git a/app/handler.py b/app/handler.py
--- a/app/handler.py
+++ b/app/handler.py
@@ -1,5 +1,8 @@
+def handle_request():
+    try:
+        do_something()
+    except:
+        pass
"""


class TestPRReviewerEngine(unittest.TestCase):

    def test_clean_diff_returns_approve_5_of_5(self):
        """Test 1: Clean code diff -> returns APPROVE with 5/5 confidence."""
        engine = PRReviewEngine(CLEAN_DIFF)
        result = engine.analyze()

        self.assertEqual(result.recommendation, Recommendation.APPROVE)
        self.assertEqual(result.confidence_score, "5/5")
        self.assertEqual(len([f for f in result.findings if f.severity == Severity.CRITICAL]), 0)
        self.assertTrue(result.has_test_changes)
        self.assertEqual(result.files_changed, 2)

    def test_vulnerable_diff_returns_request_changes(self):
        """Test 2: Vulnerable diff (hardcoded API key + raw SQL query) -> returns REQUEST_CHANGES with Critical findings."""
        engine = PRReviewEngine(VULNERABLE_DIFF)
        result = engine.analyze()

        self.assertEqual(result.recommendation, Recommendation.REQUEST_CHANGES)
        self.assertEqual(result.confidence_score, "5/5")

        critical_findings = [f for f in result.findings if f.severity == Severity.CRITICAL]
        self.assertGreaterEqual(len(critical_findings), 2)

        descriptions = [f.description for f in critical_findings]
        self.assertTrue(any("API Secret Key" in d or "API Key" in d for d in descriptions))
        self.assertTrue(any("SQL Injection" in d for d in descriptions))

    def test_shell_injection_and_path_traversal_detection(self):
        """Verify shell execution and path traversal vulnerability detections."""
        engine = PRReviewEngine(SHELL_AND_PATH_DIFF)
        result = engine.analyze()

        critical_findings = [f for f in result.findings if f.severity == Severity.CRITICAL]
        self.assertGreaterEqual(len(critical_findings), 2)
        descriptions = [f.description for f in critical_findings]
        self.assertTrue(any("shell execution" in d.lower() for d in descriptions))
        self.assertTrue(any("path traversal" in d.lower() for d in descriptions))

    def test_quality_and_exception_handling(self):
        """Verify detection of bare except and silent exception swallowing."""
        engine = PRReviewEngine(QUALITY_ISSUES_DIFF)
        result = engine.analyze()

        warning_findings = [f for f in result.findings if f.severity == Severity.WARNING]
        self.assertTrue(any("except" in f.description.lower() for f in warning_findings))

    def test_structured_markdown_formatting_integrity(self):
        """Test 4: Structured markdown formatting integrity."""
        engine = PRReviewEngine(VULNERABLE_DIFF)
        result = engine.analyze()
        md_output = MarkdownReviewFormatter.format(result)

        # Check required markdown sections and headers
        self.assertIn("# Pull Request Review Report", md_output)
        self.assertIn("**Recommendation:** `REQUEST_CHANGES`", md_output)
        self.assertIn("**Confidence Score:** 5/5", md_output)
        self.assertIn("## Executive Summary", md_output)
        self.assertIn("| Metric | Value |", md_output)
        self.assertIn("| **Files Changed** |", md_output)
        self.assertIn("| **Critical Vulnerabilities** |", md_output)
        self.assertIn("## Detailed Findings", md_output)
        self.assertIn("| Severity | Category | File | Line | Description |", md_output)
        self.assertIn("`Critical`", md_output)
        self.assertIn("## Actionable Suggestions & Patches", md_output)

    def test_empty_diff_handling(self):
        """Verify empty diff is safely parsed and approved."""
        engine = PRReviewEngine("")
        result = engine.analyze()
        self.assertEqual(result.recommendation, Recommendation.APPROVE)
        self.assertEqual(result.files_changed, 0)
        self.assertEqual(result.confidence_score, "5/5")
        md_output = MarkdownReviewFormatter.format(result)
        self.assertIn("No critical issues", md_output)

    def test_missing_tests_warning(self):
        """Verify warning when code is added without test changes."""
        diff_no_test = """diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,3 +1,6 @@
+def new_feature():
+    return "hello"
+"""
        engine = PRReviewEngine(diff_no_test)
        result = engine.analyze()
        self.assertEqual(result.recommendation, Recommendation.COMMENT)
        self.assertTrue(any(f.category == Category.TESTING and f.severity == Severity.WARNING for f in result.findings))


class TestPRReviewerCLI(unittest.TestCase):

    def test_stdin_piping_and_cli_arguments(self):
        """Test 3: Stdin piping and CLI argument parsing."""
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "pr_reviewer.py")

        # Test stdin piping
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=CLEAN_DIFF)
        self.assertEqual(process.returncode, 0)
        self.assertIn("**Recommendation:** `APPROVE`", stdout)
        self.assertIn("**Confidence Score:** 5/5", stdout)

        # Test file argument passing
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".diff") as tmp:
            tmp.write(VULNERABLE_DIFF)
            tmp_path = tmp.name

        try:
            # Positional arg
            res_pos = subprocess.run(
                [sys.executable, script_path, tmp_path],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_pos.returncode, 0)
            self.assertIn("`REQUEST_CHANGES`", res_pos.stdout)

            # Flag --diff
            res_flag = subprocess.run(
                [sys.executable, script_path, "--diff", tmp_path],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_flag.returncode, 0)
            self.assertIn("`REQUEST_CHANGES`", res_flag.stdout)

            # Flag --strict on vulnerable diff should exit with 1
            res_strict = subprocess.run(
                [sys.executable, script_path, "--strict", tmp_path],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_strict.returncode, 1)

            # Output to file
            with tempfile.NamedTemporaryFile("r", delete=False, suffix=".md") as out_file:
                out_path = out_file.name

            try:
                res_out = subprocess.run(
                    [sys.executable, script_path, "--diff", tmp_path, "-o", out_path],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res_out.returncode, 0)
                with open(out_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.assertIn("# Pull Request Review Report", content)
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
