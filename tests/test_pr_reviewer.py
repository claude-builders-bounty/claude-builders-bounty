from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEWER_PATH = ROOT / "agents" / "pr-reviewer" / "claude_review.py"
FIXTURE_DIR = ROOT / "agents" / "pr-reviewer" / "fixtures"

spec = importlib.util.spec_from_file_location("claude_review", REVIEWER_PATH)
reviewer = importlib.util.module_from_spec(spec)
sys.modules["claude_review"] = reviewer
assert spec.loader is not None
spec.loader.exec_module(reviewer)


def test_parse_diff_summarizes_files_and_risks() -> None:
    diff_text = (FIXTURE_DIR / "sample_pr.diff").read_text(encoding="utf-8")
    files = reviewer.parse_diff(diff_text)

    assert [change.path for change in files] == ["src/profile.py", "tests/test_profile.py"]
    assert files[0].additions == 5
    assert files[0].deletions == 1
    assert any("eval" in line.lower() for line in files[0].risky_lines)


def test_render_review_includes_required_sections() -> None:
    metadata = json.loads((FIXTURE_DIR / "sample_pr_metadata.json").read_text(encoding="utf-8"))
    diff_text = (FIXTURE_DIR / "sample_pr.diff").read_text(encoding="utf-8")
    output = reviewer.review_from_diff("https://github.com/example/project/pull/1", metadata, diff_text)

    assert "# PR Review: Add profile bio field" in output
    assert "## Summary" in output
    assert "## Identified Risks" in output
    assert "## Improvement Suggestions" in output
    assert "## Testing Gaps" in output
    assert "## Confidence Score" in output
    assert "Medium (" in output
    assert "## Suggested GitHub Comment" in output
    assert "tests/test_profile.py" in output


def test_cli_writes_output_file(tmp_path: Path) -> None:
    output_path = tmp_path / "review.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REVIEWER_PATH),
            "--pr",
            "https://github.com/example/project/pull/1",
            "--metadata-file",
            str(FIXTURE_DIR / "sample_pr_metadata.json"),
            "--diff-file",
            str(FIXTURE_DIR / "sample_pr.diff"),
            "--output",
            str(output_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    output = output_path.read_text(encoding="utf-8")
    assert "## Summary" in output
    assert "## Identified Risks" in output
    assert "## Improvement Suggestions" in output
    assert "## Confidence Score" in output
    assert "## Suggested GitHub Comment" in output_path.read_text(encoding="utf-8")
