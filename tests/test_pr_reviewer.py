import subprocess
import sys
from pathlib import Path

from agents.pr_reviewer_import import load_module

ROOT = Path(__file__).resolve().parents[1]
reviewer = load_module(ROOT / "agents" / "pr-reviewer" / "claude_review.py")


def test_github_pr_diff_url():
    assert reviewer.github_pr_diff_url("https://github.com/owner/repo/pull/123") == "https://github.com/owner/repo/pull/123.diff"


def test_render_review_has_required_sections():
    diff = (ROOT / "samples" / "pr-reviewer" / "sample_pr_with_tests.diff").read_text()
    output = reviewer.render_review("sample", diff)
    assert "### Summary of changes" in output
    assert "### Identified risks" in output
    assert "### Improvement suggestions" in output
    assert "### Confidence score" in output
    assert "High" in output or "Medium" in output


def test_config_without_tests_flags_risks():
    diff = (ROOT / "samples" / "pr-reviewer" / "sample_config_change.diff").read_text()
    output = reviewer.render_review("sample", diff)
    assert "No obvious test updates" in output
    assert "Dependency/lockfile" in output or "Configuration/workflow" in output


def test_cli_diff_file_outputs_markdown():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "agents" / "pr-reviewer" / "claude_review.py"), "--diff-file", str(ROOT / "samples" / "pr-reviewer" / "sample_pr_with_tests.diff")],
        check=True,
        text=True,
        capture_output=True,
    )
    assert proc.stdout.startswith("## Claude PR Review")
    assert "Confidence score" in proc.stdout
