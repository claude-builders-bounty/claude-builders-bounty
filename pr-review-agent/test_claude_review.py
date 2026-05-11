#!/usr/bin/env python3
"""Basic regression test for the PR review agent."""

from __future__ import annotations

import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLI = ROOT / "claude-review"


def load_cli_module():
    loader = SourceFileLoader("claude_review", str(CLI))
    spec = importlib.util.spec_from_loader("claude_review", loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["claude_review"] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_cli_module()
    diff = """\
diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 print("hello")
+api_key = "example"
+eval(user_input)
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 3333333..4444444 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1 +1,2 @@
 name: CI
+on: pull_request
"""

    review = module.render_review("https://github.com/example/repo/pull/1", diff)
    assert "### Summary" in review
    assert "### Identified Risks" in review
    assert "credential-like" in review
    assert "dynamic code execution" in review
    assert "Workflow changes" in review
    assert "**Low**" in review
    print("test_claude_review.py passed")


if __name__ == "__main__":
    main()
