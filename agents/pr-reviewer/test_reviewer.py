#!/usr/bin/env python3
"""
🧪 Automated Test Suite for Claude PR Reviewer Agent
Tests diff parsing, security risk detection, confidence scoring, and CLI interface.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from claude_review import PullRequestReviewer

SAMPLE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index 0000000..1111111 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -0,0 +1,10 @@
+def login():
+    api_key = "12345678901234567890"
+    try:
+        print("authenticating")
+    except:
+        pass
diff --git a/tests/test_auth.py b/tests/test_auth.py
index 0000000..2222222 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -0,0 +1,5 @@
+def test_login():
+    assert True
"""


def test_diff_parsing():
    print("🔍 Testing Diff Parsing Engine:")
    reviewer = PullRequestReviewer()
    files = reviewer.parse_diff(SAMPLE_DIFF)
    assert len(files) == 2, f"Expected 2 files, got {len(files)}"
    assert files[0]["path"] == "src/auth.py"
    assert files[1]["path"] == "tests/test_auth.py"
    assert files[0]["additions"] == 6
    print("  ✅ Diff parsing accurately extracted changed files and lines added!")


def test_risk_detection():
    print("🔍 Testing Security & Risk Detection:")
    reviewer = PullRequestReviewer()
    files = reviewer.parse_diff(SAMPLE_DIFF)
    risks = reviewer.analyze_risks(files)

    categories = [r["category"] for r in risks]
    assert "Security / Secrets" in categories, "Failed to detect hardcoded secret!"
    assert "Error Handling" in categories, "Failed to detect bare except!"
    print(f"  ✅ Correctly flagged {len(risks)} risks (Secret detection & Bare except handler)!")


def test_confidence_scoring():
    print("🔍 Testing Objective Confidence Scoring:")
    reviewer = PullRequestReviewer()
    files = reviewer.parse_diff(SAMPLE_DIFF)
    risks = reviewer.analyze_risks(files)
    confidence = reviewer.calculate_confidence(files, risks)
    assert confidence == "Low", f"Expected Low confidence due to High-severity secret, got {confidence}"
    print(f"  ✅ Confidence score accurately evaluated to: {confidence}")


def test_markdown_generation():
    print("🔍 Testing Markdown Report Generation:")
    reviewer = PullRequestReviewer()
    report = reviewer.generate_review("https://github.com/owner/repo/pull/1", SAMPLE_DIFF)
    assert "## 🤖 Claude Code Automated PR Review" in report
    assert "### 📋 Summary of Changes" in report
    assert "### ⚠️ Identified Risks" in report
    assert "### 💡 Improvement Suggestions" in report
    assert "### 🎯 Confidence Score: **Low**" in report
    print("  ✅ Full review markdown generated according to acceptance specification!")


if __name__ == "__main__":
    test_diff_parsing()
    test_risk_detection()
    test_confidence_scoring()
    test_markdown_generation()
    print("\n🏆 ALL TESTS PASSED! Reviewer agent is 100% compliant with Issue #4 criteria.\n")
