#!/usr/bin/env python3
from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("claude-review")
loader = importlib.machinery.SourceFileLoader("claude_review", str(MODULE_PATH))
spec = importlib.util.spec_from_loader("claude_review", loader)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_parse_pr_url() -> None:
    ref = module.parse_pr_url("https://github.com/owner/repo/pull/123")
    assert ref.owner == "owner"
    assert ref.repo == "repo"
    assert ref.number == 123


def test_render_review_shape() -> None:
    pr = {
        "title": "Add tests for widget parser",
        "state": "closed",
        "merged": True,
        "additions": 42,
        "deletions": 7,
        "changed_files": 2,
    }
    files = [
        {"filename": "src/widget.py", "additions": 20, "deletions": 5},
        {"filename": "tests/test_widget.py", "additions": 22, "deletions": 2},
    ]
    review = module.render_review("https://github.com/owner/repo/pull/123", pr, files)
    assert "## Summary of Changes" in review
    assert "## Identified Risks" in review
    assert "## Improvement Suggestions" in review
    assert "## Confidence Score: High" in review


if __name__ == "__main__":
    test_parse_pr_url()
    test_render_review_shape()
    print("tests_ok=true")
