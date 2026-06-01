#!/usr/bin/env python3
"""Smoke tests for the PR review agent."""

from __future__ import annotations

import tempfile
from pathlib import Path

from claude_review import build_diff_url, main, parse_diff, render_markdown

ROOT = Path(__file__).resolve().parents[1]

CODE_DIFF = """diff --git a/app/auth.py b/app/auth.py
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,3 +1,6 @@
 def can_view(user):
-    return True
+    if user.role == "admin":
+        return True
+    return False
"""

DOC_DIFF = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Demo
+More setup notes.
"""


def test_parse_diff_counts_files_and_lines() -> None:
    stats = parse_diff(CODE_DIFF)

    assert len(stats.files) == 1
    assert stats.additions == 3
    assert stats.deletions == 1
    assert stats.files[0].path == "app/auth.py"


def test_render_flags_code_without_tests() -> None:
    review = render_markdown(parse_diff(CODE_DIFF), "sample")

    assert "Application code changed without a matching test update" in review
    assert "Security-sensitive paths or names changed" in review
    assert "### Confidence" in review
    assert "Medium" in review


def test_docs_only_review_is_high_confidence() -> None:
    review = render_markdown(parse_diff(DOC_DIFF), "docs")

    assert "documentation-only" in review
    assert "Low functional risk" in review
    assert "High" in review


def test_extensionless_readme_is_documentation() -> None:
    diff = """diff --git a/README b/README
--- a/README
+++ b/README
@@ -1 +1,2 @@
 Hello World!
+Setup note.
"""
    review = render_markdown(parse_diff(diff), "readme")

    assert "documentation-only" in review
    assert "High" in review


def test_build_diff_url_accepts_github_pr_url() -> None:
    assert (
        build_diff_url("https://github.com/octocat/Hello-World/pull/6")
        == "https://github.com/octocat/Hello-World/pull/6.diff"
    )


def test_cli_rejects_post_comment_without_pr() -> None:
    try:
        main(["--diff-file", "sample.diff", "--post-comment", "--github-token", "token"])
    except SystemExit as exc:
        result = exc.code
    else:
        result = 0

    assert result == 2


def test_cli_rejects_post_comment_without_token() -> None:
    try:
        main(["--pr", "https://github.com/octocat/Hello-World/pull/6", "--post-comment"])
    except SystemExit as exc:
        result = exc.code
    else:
        result = 0

    assert result == 2


def test_cli_writes_output_from_diff_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        diff_path = root / "sample.diff"
        output_path = root / "review.md"
        diff_path.write_text(DOC_DIFF, encoding="utf-8")

        result = main(["--diff-file", str(diff_path), "--output", str(output_path)])

        assert result == 0
        output = output_path.read_text(encoding="utf-8")
        assert output.startswith("## PR Review")
        assert "### Identified Risks" in output
        assert "### Improvement Suggestions" in output


def test_claude_sub_agent_contract_is_present() -> None:
    agent = ROOT / ".claude" / "agents" / "pr-reviewer.md"
    content = agent.read_text(encoding="utf-8")

    assert "name: pr-reviewer" in content
    assert "### Identified Risks" in content
    assert "### Improvement Suggestions" in content
    assert "### Confidence" in content


if __name__ == "__main__":
    test_parse_diff_counts_files_and_lines()
    test_render_flags_code_without_tests()
    test_docs_only_review_is_high_confidence()
    test_extensionless_readme_is_documentation()
    test_build_diff_url_accepts_github_pr_url()
    test_cli_rejects_post_comment_without_pr()
    test_cli_rejects_post_comment_without_token()
    test_cli_writes_output_from_diff_file()
    test_claude_sub_agent_contract_is_present()
    print("ok")
