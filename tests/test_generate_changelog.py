"""Unit tests for tools/generate_changelog.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_changelog  # noqa: E402


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True, text=True)


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    return repo


def commit_file(repo: Path, name: str, message: str) -> None:
    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", message)


def test_generate_changelog_returns_nonempty_string(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "sample.txt", "initial sample commit")

    output = tmp_path / "CHANGELOG.md"
    result = generate_changelog.generate_changelog(repo, output)

    assert isinstance(result, str)
    assert result.strip()
    assert len(result) > 0


def test_groups_by_month_when_no_tags(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "a.txt", "add feature a")
    git(repo, "commit", "--allow-empty", "-m", "fix bug in parser")

    output = repo / "CHANGELOG.md"
    generate_changelog.generate_changelog(repo, output)
    text = output.read_text(encoding="utf-8")

    assert "# Changelog" in text
    assert "## [" in text
    assert "- add feature a" in text
    assert "- fix bug in parser" in text


def test_groups_by_tag_versions(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "a.txt", "add initial module")
    git(repo, "tag", "v0.1.0")
    git(repo, "commit", "--allow-empty", "-m", "fix crash on startup")
    git(repo, "tag", "v0.2.0")
    git(repo, "commit", "--allow-empty", "-m", "update docs")

    output = repo / "CHANGELOG.md"
    generate_changelog.generate_changelog(repo, output)
    text = output.read_text(encoding="utf-8")

    assert "## [Unreleased]" in text
    assert "- update docs" in text
    assert "## [v0.2.0]" in text
    assert "- fix crash on startup" in text
    assert "## [v0.1.0]" in text
    assert "- add initial module" in text


def test_output_flag(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md", "add readme")

    custom_output = tmp_path / "docs" / "HISTORY.md"
    generate_changelog.generate_changelog(repo, custom_output)

    assert custom_output.exists()
    assert "- add readme" in custom_output.read_text(encoding="utf-8")


def test_main_cli_with_output_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md", "add readme")

    output = tmp_path / "out" / "CHANGELOG.md"
    monkeypatch.chdir(repo)
    exit_code = generate_changelog.main(["--output", str(output), str(repo)])

    assert exit_code == 0
    assert output.exists()


def test_empty_repo_produces_header_only(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    output = repo / "CHANGELOG.md"
    generate_changelog.generate_changelog(repo, output)
    assert output.read_text(encoding="utf-8") == "# Changelog\n"
