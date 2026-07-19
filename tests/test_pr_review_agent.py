"""Tests for the PR review agent (Issue #4)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from solutions.issue_4_pr_review.pr_review_agent import (
    MAX_TOTAL_DIFF_CHARS,
    DiffChunk,
    ReviewResult,
    generate_review_report,
    parse_diff_into_chunks,
    run_review,
    static_review,
)


# ──────────────────────────────────────────────────────────────────── #
# parse_diff_into_chunks
# ──────────────────────────────────────────────────────────────────── #
def test_parse_empty_diff():
    chunks = parse_diff_into_chunks("")
    assert chunks == []


def test_parse_single_file_diff():
    diff = "diff --git a/src/main.py b/src/main.py\n+print('hello')\n"
    chunks = parse_diff_into_chunks(diff)
    assert len(chunks) == 1
    assert "main.py" in chunks[0].filename
    assert "print('hello')" in chunks[0].content


def test_parse_multiple_file_diffs():
    diff = """diff --git a/file1.py b/file1.py
+change1
diff --git a/file2.py b/file2.py
+change2"""
    chunks = parse_diff_into_chunks(diff)
    assert len(chunks) == 2
    assert "file1.py" in chunks[0].filename
    assert "file2.py" in chunks[1].filename


def test_parse_large_diff_truncates():
    large_diff = "diff --git a/big.py b/big.py\n" + ("+line\n" * 5000)
    chunks = parse_diff_into_chunks(large_diff, max_chunk_chars=1000)
    assert len(chunks) == 1
    assert chunks[0].is_truncated is True
    assert len(chunks[0].content) <= 1100  # chunk + truncation message


def test_parse_whitespace_only_diff():
    chunks = parse_diff_into_chunks("   \n  \n  ")
    assert chunks == []


# ──────────────────────────────────────────────────────────────────── #
# static_review
# ──────────────────────────────────────────────────────────────────── #
def test_static_review_detects_todo():
    chunk = DiffChunk(
        filename="main.py",
        content="diff --git a/main.py b/main.py\n+    # TODO: fix this later\n",
    )
    review = static_review(chunk)
    assert "TODO" in review
    assert "main.py" in review


def test_static_review_detects_fixme():
    chunk = DiffChunk(
        filename="app.py",
        content="diff --git a/app.py b/app.py\n+    # FIXME: urgent bug\n",
    )
    review = static_review(chunk)
    assert "FIXME" in review


def test_static_review_detects_potential_secret():
    chunk = DiffChunk(
        filename="config.py",
        content="diff --git a/config.py b/config.py\n+api_key = 'sk-abc123def456'\n",
    )
    review = static_review(chunk)
    assert "api_key" in review.lower() or "secret" in review.lower() or "🔒" in review


def test_static_review_detects_print_statements():
    chunk = DiffChunk(
        filename="debug.py",
        content="diff --git a/debug.py b/debug.py\n+    print('debugging')\n+    console.log('test')\n",
    )
    review = static_review(chunk)
    assert "print" in review.lower() or "debug" in review.lower()


def test_static_review_clean_diff_no_issues():
    chunk = DiffChunk(
        filename="clean.py",
        content="diff --git a/clean.py b/clean.py\n+def add(a, b):\n+    return a + b\n",
    )
    review = static_review(chunk)
    assert "No issues detected" in review or "None" in review


def test_static_review_shows_line_counts():
    chunk = DiffChunk(
        filename="main.py",
        content="diff --git a/main.py b/main.py\n+line1\n+line2\n-line0\n",
    )
    review = static_review(chunk)
    assert "+2" in review
    assert "-1" in review


def test_static_review_notes_truncation():
    chunk = DiffChunk(
        filename="big.py",
        content="diff --git a/big.py b/big.py\n+line\n",
        is_truncated=True,
    )
    review = static_review(chunk)
    assert "truncated" in review.lower()


# ──────────────────────────────────────────────────────────────────── #
# generate_review_report
# ──────────────────────────────────────────────────────────────────── #
def test_report_has_header():
    results = []
    report = generate_review_report(results)
    assert "# 📋 Pull Request Review" in report
    assert "Summary" in report


def test_report_includes_pr_url():
    results = []
    report = generate_review_report(results, pr_url="https://github.com/owner/repo/pull/123")
    assert "https://github.com/owner/repo/pull/123" in report


def test_report_includes_file_reviews():
    results = [
        ReviewResult(filename="main.py", review_text="### File: main.py\nLooks good"),
        ReviewResult(filename="test.py", review_text="### File: test.py\nNeeds tests"),
    ]
    report = generate_review_report(results)
    assert "main.py" in report
    assert "test.py" in report
    assert "Files reviewed:** 2" in report


def test_report_counts_errors():
    results = [
        ReviewResult(filename="ok.py", review_text="ok"),
        ReviewResult(filename="bad.py", review_text="error", error="API failed"),
    ]
    report = generate_review_report(results)
    assert "Files with errors:** 1" in report


# ──────────────────────────────────────────────────────────────────── #
# run_review (end-to-end with mocked git)
# ──────────────────────────────────────────────────────────────────── #
def test_run_review_no_diff():
    with patch("solutions.issue_4_pr_review.pr_review_agent.get_git_diff", return_value=""):
        report = run_review(output_file="/tmp/test_pr_review.md")
    assert "No changes detected" in report


def test_run_review_with_mocked_diff(tmp_path):
    mock_diff = "diff --git a/main.py b/main.py\n+print('hello')\n"
    output_file = str(tmp_path / "PR_REVIEW.md")
    with patch("solutions.issue_4_pr_review.pr_review_agent.get_git_diff", return_value=mock_diff):
        report = run_review(output_file=output_file)
    assert "main.py" in report
    assert Path(output_file).exists()


def test_run_review_truncates_large_diff(tmp_path):
    large_diff = "x" * (MAX_TOTAL_DIFF_CHARS + 10000)
    output_file = str(tmp_path / "PR_REVIEW.md")
    with patch("solutions.issue_4_pr_review.pr_review_agent.get_git_diff", return_value=large_diff):
        report = run_review(output_file=output_file)
    # Should not crash; diff should be truncated
    assert isinstance(report, str)
    assert len(report) > 0


def test_run_review_writes_output_file(tmp_path):
    mock_diff = "diff --git a/app.py b/app.py\n+x = 1\n"
    output_file = str(tmp_path / "review.md")
    with patch("solutions.issue_4_pr_review.pr_review_agent.get_git_diff", return_value=mock_diff):
        run_review(output_file=output_file)
    assert Path(output_file).exists()
    content = Path(output_file).read_text()
    assert "Pull Request Review" in content
