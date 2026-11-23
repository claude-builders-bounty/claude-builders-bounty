#!/usr/bin/env python3
"""Tests for the git changelog generator."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from generate_changelog import (
    classify_commit,
    format_release_section,
    main,
    prepend_to_existing,
    render_full_changelog,
)


def run_cmd(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_git_repo(repo_dir: str) -> None:
    run_cmd(["git", "init", "-b", "main"], cwd=repo_dir)
    run_cmd(["git", "config", "user.name", "Tester"], cwd=repo_dir)
    run_cmd(["git", "config", "user.email", "tester@example.com"], cwd=repo_dir)


def test_classify_commit() -> None:
    cases = [
        ("feat: add dark mode support", ("Added", "Add dark mode support")),
        ("feat(ui): add new button component", ("Added", "Add new button component")),
        ("Add support for python 3.12", ("Added", "Support for python 3.12")),
        ("fix: resolve null pointer exception", ("Fixed", "Resolve null pointer exception")),
        ("fix(auth): handle expired tokens gracefully", ("Fixed", "Handle expired tokens gracefully")),
        ("resolve memory leak in worker", ("Fixed", "Memory leak in worker")),
        ("remove: drop deprecated v1 endpoints", ("Removed", "Drop deprecated v1 endpoints")),
        ("delete unused helper functions", ("Removed", "Unused helper functions")),
        ("refactor: extract helper function", ("Changed", "Extract helper function")),
        ("perf: cache database query results", ("Changed", "Cache database query results")),
        ("docs: update README setup instructions", ("Changed", "Update README setup instructions")),
        ("chore: upgrade dependencies", ("Changed", "Upgrade dependencies")),
        ("random commit without prefix", ("Changed", "random commit without prefix")),
    ]

    for input_msg, expected in cases:
        actual = classify_commit(input_msg)
        assert actual == expected, f"Failed for '{input_msg}': expected {expected}, got {actual}"


def test_full_git_repo_changelog_generation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_path = Path(tmp)
        init_git_repo(str(repo_path))

        # Commit 1: base commit
        (repo_path / "file.txt").write_text("v1", encoding="utf-8")
        run_cmd(["git", "add", "."], cwd=str(repo_path))
        run_cmd(["git", "commit", "-m", "Initial commit"], cwd=str(repo_path))
        run_cmd(["git", "tag", "v1.0.0"], cwd=str(repo_path))

        # Commits after tag v1.0.0
        (repo_path / "auth.py").write_text("def auth(): pass", encoding="utf-8")
        run_cmd(["git", "add", "."], cwd=str(repo_path))
        run_cmd(["git", "commit", "-m", "feat: add user authentication flow"], cwd=str(repo_path))

        (repo_path / "bug.py").write_text("fixed", encoding="utf-8")
        run_cmd(["git", "add", "."], cwd=str(repo_path))
        run_cmd(["git", "commit", "-m", "fix: prevent crash on empty username"], cwd=str(repo_path))

        (repo_path / "legacy.py").unlink(missing_ok=True)
        run_cmd(["git", "commit", "--allow-empty", "-m", "remove: remove deprecated v1 api"], cwd=str(repo_path))

        (repo_path / "query.py").write_text("optimized", encoding="utf-8")
        run_cmd(["git", "add", "."], cwd=str(repo_path))
        run_cmd(["git", "commit", "-m", "refactor: optimize database query builder"], cwd=str(repo_path))

        output_file = repo_path / "CHANGELOG.md"

        # Execute changelog generator
        ret = main(["--output", str(output_file)], cwd=str(repo_path))
        assert ret == 0, f"Expected main to return 0, got {ret}"

        content = output_file.read_text(encoding="utf-8")
        assert "# Changelog" in content
        assert "## [Unreleased]" in content
        assert "### Added" in content
        assert "Add user authentication flow" in content
        assert "### Fixed" in content
        assert "Prevent crash on empty username" in content
        assert "### Changed" in content
        assert "Optimize database query builder" in content
        assert "### Removed" in content
        assert "Remove deprecated v1 api" in content
        assert "Initial commit" not in content  # Belongs to v1.0.0, excluded by default tag boundary


def test_prepend_to_existing_changelog() -> None:
    existing_changelog = """# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-01-01

### Added
- Initial project structure (`1111111`)
"""
    new_release = """## [1.1.0] - 2026-02-01

### Added
- New dashboard feature (`2222222`)
"""
    result = prepend_to_existing(existing_changelog, new_release)
    assert "## [1.1.0] - 2026-02-01" in result
    assert result.index("## [1.1.0]") < result.index("## [1.0.0]")
    assert "Initial project structure (`1111111`)" in result


def test_repo_without_tags() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_path = Path(tmp)
        init_git_repo(str(repo_path))

        (repo_path / "hello.py").write_text("print('hi')", encoding="utf-8")
        run_cmd(["git", "add", "."], cwd=str(repo_path))
        run_cmd(["git", "commit", "-m", "feat: first feature without tag"], cwd=str(repo_path))

        output_file = repo_path / "CHANGELOG.md"
        ret = main(["--output", str(output_file)], cwd=str(repo_path))
        assert ret == 0

        content = output_file.read_text(encoding="utf-8")
        assert "### Added" in content
        assert "First feature without tag" in content


if __name__ == "__main__":
    test_classify_commit()
    test_full_git_repo_changelog_generation()
    test_prepend_to_existing_changelog()
    test_repo_without_tags()
    print("ALL TESTS PASSED: OK")
