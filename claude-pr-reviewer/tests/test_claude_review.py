#!/usr/bin/env python3
"""Unit tests for claude-review helpers."""

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "claude-review"
loader = importlib.machinery.SourceFileLoader("claude_review", str(SCRIPT))
spec = importlib.util.spec_from_loader("claude_review", loader)
module = importlib.util.module_from_spec(spec)
assert spec is not None
assert spec.loader is not None
sys.modules["claude_review"] = module
spec.loader.exec_module(module)


def test_parse_pr_url():
    pr = module.parse_pr_url("https://github.com/example/repo/pull/123")
    assert pr.owner == "example"
    assert pr.repo == "repo"
    assert pr.number == "123"
    assert pr.diff_url == "https://github.com/example/repo/pull/123.diff"


def test_heuristic_review_has_required_sections():
    diff = """diff --git a/src/auth.ts b/src/auth.ts
+++ b/src/auth.ts
@@ -1 +1,2 @@
+export function login() { return true }
diff --git a/package-lock.json b/package-lock.json
+++ b/package-lock.json
@@ -1 +1,2 @@
+{}
"""
    pr = module.parse_pr_url("https://github.com/example/repo/pull/123")
    review = module.heuristic_review(pr, diff)
    assert "## Summary of changes" in review
    assert "## Identified risks" in review
    assert "## Improvement suggestions" in review
    assert "## Confidence score" in review
    assert "Medium" in review
