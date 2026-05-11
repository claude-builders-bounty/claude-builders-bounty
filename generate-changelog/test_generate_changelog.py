#!/usr/bin/env python3
"""Regression tests for generate_changelog.py."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("generate_changelog.py")


def run(command: list[str], cwd: Path) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def commit(repo: Path, message: str) -> None:
    marker = repo / "file.txt"
    marker.write_text(marker.read_text(encoding="utf-8") + message + "\n", encoding="utf-8")
    run(["git", "add", "file.txt"], repo)
    run(["git", "commit", "-m", message], repo)


def make_repo() -> Path:
    temp = Path(tempfile.mkdtemp())
    run(["git", "init"], temp)
    run(["git", "config", "user.email", "test@example.com"], temp)
    run(["git", "config", "user.name", "Test User"], temp)
    (temp / "file.txt").write_text("initial\n", encoding="utf-8")
    run(["git", "add", "file.txt"], temp)
    run(["git", "commit", "-m", "feat: initial release"], temp)
    run(["git", "tag", "v1.0.0"], temp)
    commit(temp, "feat: add import command")
    commit(temp, "fix: repair changelog grouping")
    commit(temp, "remove obsolete flag")
    commit(temp, "docs: update usage notes")
    return temp


def test_changelog_since_latest_tag() -> None:
    repo = make_repo()
    output = run(["python", str(SCRIPT), "--repo", str(repo), "--dry-run"], repo)

    assert "Changes since `v1.0.0`" in output
    assert "Initial release" not in output
    assert "Add import command" in output
    assert "Repair changelog grouping" in output
    assert "Remove obsolete flag" in output
    assert "Update usage notes" in output


if __name__ == "__main__":
    test_changelog_since_latest_tag()
    print("All tests passed.")
