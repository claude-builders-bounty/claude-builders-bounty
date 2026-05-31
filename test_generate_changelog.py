#!/usr/bin/env python3
"""Smoke tests for generate_changelog.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "generate_changelog.py"


def run(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout


def git(repo: Path, *args: str) -> str:
    return run(["git", *args], repo)


def test_generates_expected_sections() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test User")

        (repo / "app.txt").write_text("hello\n", encoding="utf-8")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "feat: add greeting file")

        (repo / "app.txt").write_text("hello fixed\n", encoding="utf-8")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "fix: correct greeting")

        (repo / "old.txt").write_text("remove me\n", encoding="utf-8")
        git(repo, "add", "old.txt")
        git(repo, "commit", "-m", "chore: add temporary file")

        (repo / "old.txt").unlink()
        git(repo, "add", "old.txt")
        git(repo, "commit", "-m", "remove temporary file")

        run([sys.executable, str(SCRIPT), "--repo", str(repo)], repo)
        changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")

        assert "### Added" in changelog
        assert "- Add greeting file" in changelog
        assert "### Fixed" in changelog
        assert "- Correct greeting" in changelog
        assert "### Changed" in changelog
        assert "- Add temporary file" in changelog
        assert "### Removed" in changelog
        assert "- Remove temporary file" in changelog


if __name__ == "__main__":
    test_generates_expected_sections()
    print("ok")
