#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "bin" / "claude-review"


def main() -> int:
    test_cli_fixture_output()
    test_cli_rejects_bad_url()
    print("ok - claude-review tests")
    return 0


def test_cli_fixture_output() -> None:
    fixture = {
        "number": 123,
        "title": "Add example workflow",
        "author": {"login": "octocat"},
        "url": "https://github.com/octo/repo/pull/123",
        "baseRefName": "main",
        "headRefName": "feature/workflow",
        "additions": 24,
        "deletions": 4,
        "changedFiles": 2,
        "body": "Adds a workflow",
        "diff": "\n".join(
            [
                "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml",
                "+++ b/.github/workflows/ci.yml",
                "+name: ci",
                "+permissions: read-all",
                "diff --git a/tests/test_ci.py b/tests/test_ci.py",
                "+++ b/tests/test_ci.py",
                "+def test_ci():",
                "+    assert True",
            ]
        ),
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(CLI), "--pr", fixture["url"], "--offline-fixture", str(fixture_path)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert "## Summary of Changes" in output
    assert "## Identified Risks" in output
    assert "## Improvement Suggestions" in output
    assert "## Confidence Score:" in output
    assert "Workflow changes can affect CI permissions" in output


def test_cli_rejects_bad_url() -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), "--pr", "https://example.com/not/a/pr"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "GitHub pull request URL" in result.stderr


if __name__ == "__main__":
    raise SystemExit(main())
