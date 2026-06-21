#!/usr/bin/env python3
"""Standalone tests for scripts/generate_changelog.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_changelog.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_changelog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["generate_changelog"] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", message)


def test_generates_changelog_since_last_tag() -> None:
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test User")

        commit_file(repo, "README.md", "base\n", "chore: initial release")
        git(repo, "tag", "v1.0.0")
        commit_file(repo, "feature.txt", "feature\n", "feat: add export command")
        commit_file(repo, "bug.txt", "fix\n", "fix: repair empty tag handling")
        commit_file(repo, "api.txt", "changed\n", "refactor: simplify git log parser")
        commit_file(repo, "old.txt", "gone\n", "remove legacy shell-only flow")

        assert mod.last_tag(repo) == "v1.0.0"
        commits = mod.collect_commits(repo, "v1.0.0")
        output = mod.render_changelog(commits, "Unreleased", "v1.0.0", include_empty=True)

        assert "chore: initial release" not in output
        assert "### Added" in output and "feat: add export command" in output
        assert "### Fixed" in output and "fix: repair empty tag handling" in output
        assert "### Changed" in output and "refactor: simplify git log parser" in output
        assert "### Removed" in output and "remove legacy shell-only flow" in output


def test_main_writes_changelog() -> None:
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test User")
        commit_file(repo, "README.md", "hello\n", "feat: add project readme")

        assert mod.main(["--repo", str(repo), "--version", "v0.1.0"]) == 0
        changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## v0.1.0" in changelog
        assert "feat: add project readme" in changelog


if __name__ == "__main__":
    test_generates_changelog_since_last_tag()
    test_main_writes_changelog()
    print("generate_changelog tests passed")
