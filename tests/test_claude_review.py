#!/usr/bin/env python3
"""Smoke tests for claude-review."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "claude_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("claude_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["claude_review"] = module
    spec.loader.exec_module(module)
    return module


def test_render_review_shape() -> None:
    mod = load_module()
    diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
-print("old")
+print("new")
+# TODO follow up
diff --git a/tests/test_app.py b/tests/test_app.py
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1 @@
+def test_app(): pass
"""
    files = mod.parse_diff(diff)
    review = mod.render_review({"title": "Example PR", "number": 1}, files, diff)
    assert "## PR Review" in review
    assert "### Summary of changes" in review
    assert "### Identified risks" in review
    assert "### Improvement suggestions" in review
    assert "### Confidence score:" in review
    assert "TODO/FIXME" in review
    assert "`app.py`" in review


def test_parse_pr_url() -> None:
    mod = load_module()
    ref = mod.parse_pr_url("https://github.com/openai/codex/pull/123")
    assert ref.owner == "openai"
    assert ref.repo == "codex"
    assert ref.number == 123


if __name__ == "__main__":
    test_render_review_shape()
    test_parse_pr_url()
    print("ok")
