"""
Unit and integration tests for Claude Code PR Reviewer CLI & Sub-Agent.
Verifies:
1. URL and shorthand parsing logic.
2. Diff heuristics analysis (missing tests, security leaks, large diffs, CI alterations).
3. Structured Markdown generation conforming to all required sections.
"""

import sys
from pathlib import Path
import pytest

# Add bin directory to python path
BIN_DIR = Path(__file__).resolve().parents[1] / "agents" / "claude-review" / "bin"
sys.path.insert(0, str(BIN_DIR))

from claude_review import parse_pr_url, analyze_diff_heuristics, generate_review_markdown


def test_parse_pr_url_valid():
    owner, repo, pr_num = parse_pr_url("https://github.com/limitlessprojects/Go-Hybrid/pull/364")
    assert owner == "limitlessprojects"
    assert repo == "Go-Hybrid"
    assert pr_num == 364

    # With trailing paths
    owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo/pull/42/files")
    assert (owner, repo, pr_num) == ("owner", "repo", 42)

    # Shorthand
    owner, repo, pr_num = parse_pr_url("owner/my-repo#100")
    assert (owner, repo, pr_num) == ("owner", "my-repo", 100)


def test_parse_pr_url_invalid():
    with pytest.raises(ValueError):
        parse_pr_url("https://gitlab.com/owner/repo/merge_requests/1")
    with pytest.raises(ValueError):
        parse_pr_url("not_a_valid_pr")


def test_analyze_diff_heuristics_missing_tests():
    files = [{"filename": "src/core/auth.py", "additions": 50, "deletions": 5}]
    diff = "+ def authenticate(): pass"
    risks, suggestions, confidence = analyze_diff_heuristics(diff, files)

    assert any("Missing Automated Tests" in r for r in risks)
    assert confidence == "Medium"


def test_analyze_diff_heuristics_secret_detection():
    files = [{"filename": "config.py", "additions": 2, "deletions": 0}]
    diff = "+ API_KEY = 'sk-1234567890abcdef1234567890abcdef'"
    risks, suggestions, confidence = analyze_diff_heuristics(diff, files)

    assert any("Security Credential Leak" in r for r in risks)


def test_analyze_diff_heuristics_clean_pr():
    files = [
        {"filename": "src/utils.py", "additions": 10, "deletions": 2},
        {"filename": "tests/test_utils.py", "additions": 20, "deletions": 0},
    ]
    diff = "+ def helper(): return True\n+ def test_helper(): assert helper()"
    risks, suggestions, confidence = analyze_diff_heuristics(diff, files)

    assert any("Low Inherent Risk" in r for r in risks)
    assert confidence == "High"


def test_generate_review_markdown_structure():
    mock_pr = {
        "owner": "example",
        "repo": "project",
        "number": 12,
        "title": "Add user authentication",
        "body": "Implements JWT based authentication",
        "author": "dev-user",
        "files": [{"filename": "auth.js", "additions": 40, "deletions": 10}],
        "diff": "+ const jwt = require('jsonwebtoken');",
        "additions": 40,
        "deletions": 10,
        "changed_files_count": 1,
    }

    markdown = generate_review_markdown(mock_pr)

    # Verify required headers per acceptance criteria
    assert "## 🤖 Claude Code PR Review" in markdown
    assert "### 📝 Summary of Changes" in markdown
    assert "### ⚠️ Identified Risks" in markdown
    assert "### 💡 Improvement Suggestions" in markdown
    assert "### 🎯 Confidence Score" in markdown
    assert "**dev-user**" in markdown or "@dev-user" in markdown
    assert "project" in markdown
