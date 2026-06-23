#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "claude_review.py"
spec = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
claude_review = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["claude_review"] = claude_review
spec.loader.exec_module(claude_review)


def test_parse_pr_url():
    ref = claude_review.parse_pr_url("https://github.com/example/repo/pull/123")
    assert ref.owner == "example"
    assert ref.repo == "repo"
    assert ref.number == 123
    assert ref.diff_url.endswith("/pull/123.diff")


def test_parse_diff_counts_files_and_tests():
    diff = (ROOT / "tests" / "fixtures" / "simple.diff").read_text(encoding="utf-8")
    stats = claude_review.parse_diff(diff)
    assert stats.files == ["src/format.ts", "src/format.test.ts"]
    assert stats.additions == 4
    assert stats.deletions == 1
    assert stats.test_files == ["src/format.test.ts"]


def test_render_review_contract():
    diff = (ROOT / "tests" / "fixtures" / "simple.diff").read_text(encoding="utf-8")
    stats = claude_review.parse_diff(diff)
    ref = claude_review.parse_pr_url("https://github.com/example/repo/pull/1")
    output = claude_review.render_review(ref, stats)
    assert "### Summary of Changes" in output
    assert "### Identified Risks" in output
    assert "### Improvement Suggestions" in output
    assert "### Confidence Score" in output
    assert any(score in output for score in ["Low", "Medium", "High"])


if __name__ == "__main__":
    test_parse_pr_url()
    test_parse_diff_counts_files_and_tests()
    test_render_review_contract()
    print("tests passed")
