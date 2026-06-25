#!/usr/bin/env python3
"""Smoke tests for the changelog generator."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_changelog.py"


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    result = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result


def commit(repo: Path, filename: str, content: str, message: str) -> None:
    path = repo / filename
    path.write_text(content, encoding="utf-8")
    run(["git", "add", filename], repo)
    run(["git", "commit", "-m", message], repo)


def test_generates_categories_since_last_tag() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        run(["git", "init"], repo)
        commit(repo, "README.md", "hello\n", "feat: initial docs")
        run(["git", "tag", "v0.1.0"], repo)
        commit(repo, "feature.txt", "new\n", "feat: add export command")
        commit(repo, "bug.txt", "fix\n", "fix: repair parser edge case")
        commit(repo, "change.txt", "change\n", "docs: update usage")
        commit(repo, "removed.txt", "gone\n", "remove obsolete helper")

        result = run([sys.executable, str(SCRIPT), "--repo", str(repo)], repo)
        assert "Wrote" in result.stdout

        changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "_Generated from 4 commit(s) since `v0.1.0`._" in changelog
        assert "### Added\n- Add export command" in changelog
        assert "### Fixed\n- Repair parser edge case" in changelog
        assert "### Changed\n- Update usage" in changelog
        assert "### Removed\n- Remove obsolete helper" in changelog


if __name__ == "__main__":
    test_generates_categories_since_last_tag()
    print("ok")
