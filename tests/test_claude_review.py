"""Tests for claude-review analyzer and URL parsing."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from claude_review.analyzer import analyze_diff, render_markdown
from claude_review.github_client import parse_pr_url


def test_parse_pr_url_valid():
    owner, repo, number = parse_pr_url("https://github.com/owner/repo/pull/123")
    assert owner == "owner"
    assert repo == "repo"
    assert number == 123


def test_parse_pr_url_invalid():
    try:
        parse_pr_url("https://example.com/not-a-pr")
        assert False, "should have raised"
    except ValueError:
        pass


def test_analyze_detects_hardcoded_secret():
    files = [
        {
            "filename": "auth.py",
            "additions": 5,
            "deletions": 0,
            "patch": "+api_key = \"sk-1234567890abcdef\"\n+print(\"debug\")\n",
        }
    ]
    result = analyze_diff("", files)
    ids = [r.id for r in result.risks]
    assert "hardcoded-secret" in ids
    assert "debug-leftover" in ids
    assert result.confidence == "Medium"


def test_analyze_detects_sql_injection():
    files = [
        {
            "filename": "db.py",
            "additions": 3,
            "deletions": 0,
            "patch": "+cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n",
        }
    ]
    result = analyze_diff("", files)
    ids = [r.id for r in result.risks]
    assert "sql-injection" in ids


def test_analyze_clean_diff():
    files = [
        {
            "filename": "utils.py",
            "additions": 2,
            "deletions": 0,
            "patch": "+def add(a, b):\n+    return a + b\n",
        }
    ]
    result = analyze_diff("", files)
    assert len(result.risks) == 0
    assert result.confidence == "Low"


def test_render_markdown_structure():
    files = [
        {
            "filename": "auth.py",
            "additions": 5,
            "deletions": 0,
            "patch": "+api_key = \"sk-1234567890abcdef\"\n",
        }
    ]
    result = analyze_diff("", files)
    md = render_markdown(result, "https://github.com/o/r/pull/1", "Test PR")
    assert "## 🤖 claude-review" in md
    assert "### Summary" in md
    assert "### Identified Risks" in md
    assert "### Improvement Suggestions" in md
    assert "### Confidence" in md
    assert "Hardcoded secret" in md


def test_confidence_high_with_many_risks():
    files = [
        {
            "filename": f"f{i}.py",
            "additions": 5,
            "deletions": 0,
            "patch": "+api_key = \"sk-1234567890abcdef\"\n+eval(data)\n+os.system(cmd)\n",
        }
        for i in range(3)
    ]
    result = analyze_diff("", files)
    assert result.confidence == "High"


def test_no_tests_suggestion():
    files = [
        {
            "filename": "app.py",
            "additions": 10,
            "deletions": 0,
            "patch": "+def handler():\n+    return 42\n",
        }
    ]
    result = analyze_diff("", files)
    ids = [s.id for s in result.suggestions]
    assert "no-tests" in ids