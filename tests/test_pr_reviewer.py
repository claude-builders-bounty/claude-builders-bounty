import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "pr-reviewer")))
from reviewer import parse_pr_url, analyze_diff, format_review_markdown

def test_parse_pr_url():
    owner, repo, pr = parse_pr_url("https://github.com/facebook/react/pull/42")
    assert owner == "facebook"
    assert repo == "react"
    assert pr == "42"

def test_analyze_diff_risk_detection():
    risky_diff = "+ rm -rf /var/data\n+ DROP TABLE users;"
    res = analyze_diff(risky_diff)
    assert any("Destructive" in r for r in res["risks"])

def test_format_review_markdown():
    res = analyze_diff("+ const a = 1;")
    md = format_review_markdown({"owner": "a", "repo": "b", "number": "1"}, res)
    assert "Confidence Score" in md
    assert "Identified Risks" in md
