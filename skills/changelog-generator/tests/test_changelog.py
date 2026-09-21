#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_changelog import get_commits, parse_commit, render  # noqa: E402


def run(repo: Path, *args: str) -> None:
    subprocess.run(args, cwd=repo, check=True, text=True, capture_output=True)


def commit(repo: Path, message: str, filename: str) -> None:
    (repo / filename).write_text(message, encoding="utf-8")
    run(repo, "git", "add", filename)
    run(repo, "git", "commit", "-m", message)


def test_literal_contract_categories():
    commits = [
        parse_commit("a1", "feat(api): add endpoint"),
        parse_commit("b2", "fix: stop crash"),
        parse_commit("c3", "refactor: simplify parser"),
        parse_commit("d4", "remove: legacy mode"),
    ]
    output = render(commits)
    for section in ("Added", "Fixed", "Changed", "Removed"):
        assert f"### {section}" in output
    assert "**api**: add endpoint" in output


def test_real_git_path_uses_latest_reachable_tag(tmp_path: Path):
    repo = tmp_path / "project"
    repo.mkdir()
    run(repo, "git", "init", "-q")
    run(repo, "git", "config", "user.email", "test@example.com")
    run(repo, "git", "config", "user.name", "Test User")
    commit(repo, "feat: before release", "old.txt")
    run(repo, "git", "tag", "v1.0.0")
    commit(repo, "fix: after release", "fix.txt")
    commit(repo, "docs: explain behavior", "docs.txt")

    boundary, rows = get_commits(repo)
    assert boundary == "v1.0.0"
    assert [subject for _, subject in rows] == ["docs: explain behavior", "fix: after release"]
    assert all("\n" not in short_hash for short_hash, _ in rows)
    assert "before release" not in render([parse_commit(*row) for row in rows])


def test_repository_without_tags_uses_full_history(tmp_path: Path):
    repo = tmp_path / "untagged"
    repo.mkdir()
    run(repo, "git", "init", "-q")
    run(repo, "git", "config", "user.email", "test@example.com")
    run(repo, "git", "config", "user.name", "Test User")
    commit(repo, "initial import", "one.txt")
    commit(repo, "fix: second commit", "two.txt")
    boundary, rows = get_commits(repo)
    assert boundary is None
    assert len(rows) == 2
    assert all("\n" not in short_hash for short_hash, _ in rows)
    assert [parse_commit(*row)["category"] for row in rows] == ["Fixed", "Changed"]


def test_bash_user_path_writes_changelog(tmp_path: Path):
    repo = tmp_path / "user-project"
    repo.mkdir()
    run(repo, "git", "init", "-q")
    run(repo, "git", "config", "user.email", "test@example.com")
    run(repo, "git", "config", "user.name", "Test User")
    commit(repo, "feat: usable command", "feature.txt")
    subprocess.run(["bash", str(ROOT / "changelog.sh"), str(repo)], cwd=repo, check=True, text=True, capture_output=True)
    output = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "### Added" in output and "usable command" in output


def test_invalid_tag_fails_instead_of_false_success(tmp_path: Path):
    repo = tmp_path / "project"
    repo.mkdir()
    run(repo, "git", "init", "-q")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_changelog.py"), "--repo", str(repo), "--since-tag", "missing"],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "unknown revision" in result.stderr.lower() or "ambiguous argument" in result.stderr.lower()
