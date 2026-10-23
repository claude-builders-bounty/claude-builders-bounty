"""
Tests for Claude Code PR Reviewer Agent.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "pr-reviewer")))
import claude_review
from claude_review import parse_pr_url, analyze_diff, format_review_markdown, PRInfo

def test_parse_pr_url_valid():
    owner, repo, number = parse_pr_url("https://github.com/my-org/my-project/pull/42")
    assert owner == "my-org"
    assert repo == "my-project"
    assert number == 42

def test_parse_pr_url_invalid():
    with pytest.raises(ValueError):
        parse_pr_url("https://github.com/my-org/my-project/issues/42")

def test_analyze_diff_risk_detection():
    mock_diff = (
        "diff --git a/config.py b/config.py\n"
        "--- a/config.py\n"
        "+++ b/config.py\n"
        "+ API_KEY = 'ghp_123456789012345678901234567890123456'\n"
        "+ os.system('rm -rf /tmp/data')\n"
    )
    pr = PRInfo(
        owner="test-owner",
        repo="test-repo",
        number=1,
        title="feat: add dangerous operations",
        body="test pr body",
        author="alice",
        base_ref="main",
        head_ref="feat/branch",
        additions=2,
        deletions=0,
        changed_files=1,
        diff_text=mock_diff
    )

    analysis = analyze_diff(pr)
    assert len(analysis["risks"]) >= 2
    assert any("Hardcoded Secrets" in r for r in analysis["risks"])
    assert any("Destructive File Operation" in r for r in analysis["risks"])
    assert analysis["confidence_score"] == "Low"

def test_analyze_diff_clean_pr():
    mock_diff = (
        "diff --git a/math_utils.py b/math_utils.py\n"
        "--- a/math_utils.py\n"
        "+++ b/math_utils.py\n"
        "+def add(a: int, b: int) -> int:\n"
        "+    return a + b\n"
        "diff --git a/tests/test_math.py b/tests/test_math.py\n"
        "--- a/tests/test_math.py\n"
        "+++ b/tests/test_math.py\n"
        "+def test_add():\n"
        "+    assert add(1, 2) == 3\n"
    )
    pr = PRInfo(
        owner="test-owner",
        repo="test-repo",
        number=2,
        title="feat: add math helper",
        body="Includes tests",
        author="bob",
        base_ref="main",
        head_ref="feat/math",
        additions=6,
        deletions=0,
        changed_files=2,
        diff_text=mock_diff
    )

    analysis = analyze_diff(pr)
    assert "No critical risks identified." in analysis["risks"]
    assert analysis["confidence_score"] == "High"

def test_format_review_markdown():
    pr = PRInfo(
        owner="test-owner",
        repo="test-repo",
        number=10,
        title="docs: update readme",
        body="readme changes",
        author="carol",
        base_ref="main",
        head_ref="patch-1",
        additions=5,
        deletions=2,
        changed_files=1,
        diff_text="diff --git a/README.md b/README.md\n+hello\n"
    )
    analysis = analyze_diff(pr)
    md = format_review_markdown(pr, analysis)
    assert "## 🤖 Claude Code PR Review" in md
    assert "### 📝 Summary of Changes" in md
    assert "### ⚠️ Identified Risks" in md
    assert "### 💡 Improvement Suggestions" in md
    assert "### 🎯 Confidence Score:" in md
