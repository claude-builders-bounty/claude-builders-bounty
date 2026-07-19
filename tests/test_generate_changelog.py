"""Tests for the CHANGELOG generator (Issue #1)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from solutions.issue_1_changelog.generate_changelog import (
    Commit,
    VersionSection,
    format_commit_entry,
    generate_changelog,
    generate_markdown,
    group_commits_by_version,
    parse_commit_line,
)

SCRIPT_PATH = Path(__file__).parent.parent.parent / "solutions" / "issue-1-changelog" / "generate_changelog.py"


# ──────────────────────────────────────────────────────────────────── #
# parse_commit_line
# ──────────────────────────────────────────────────────────────────── #
def test_parse_feat_commit():
    commit = parse_commit_line("abc1234|2026-07-18T10:00:00+00:00|feat: add user authentication")
    assert commit is not None
    assert commit.type == "feat"
    assert commit.description == "add user authentication"
    assert commit.is_merge is False


def test_parse_fix_with_scope():
    commit = parse_commit_line("def5678|2026-07-18T11:00:00+00:00|fix(api): correct response status code")
    assert commit is not None
    assert commit.type == "fix"
    assert commit.scope == "api"
    assert commit.description == "correct response status code"


def test_parse_breaking_change():
    commit = parse_commit_line("ghi9012|2026-07-18T12:00:00+00:00|feat!: redesign API endpoints")
    assert commit is not None
    assert commit.type == "feat"
    assert commit.is_breaking is True


def test_parse_breaking_change_with_scope():
    commit = parse_commit_line("jkl3456|2026-07-18T13:00:00+00:00|refactor(core)!: remove deprecated methods")
    assert commit is not None
    assert commit.scope == "core"
    assert commit.is_breaking is True


def test_parse_merge_commit():
    commit = parse_commit_line("mno7890|2026-07-18T14:00:00+00:00|Merge pull request #123 from feature/branch")
    assert commit is not None
    assert commit.is_merge is True
    assert commit.type == "merge"


def test_parse_merge_branch_commit():
    commit = parse_commit_line("pqr1234|2026-07-18T15:00:00+00:00|Merge branch 'develop' into main")
    assert commit is not None
    assert commit.is_merge is True


def test_parse_non_conventional_commit():
    commit = parse_commit_line("stu5678|2026-07-18T16:00:00+00:00|updated the README file")
    assert commit is not None
    assert commit.type == "other"
    assert commit.description == "updated the README file"


def test_parse_empty_line():
    commit = parse_commit_line("")
    assert commit is None


def test_parse_malformed_line():
    commit = parse_commit_line("only one pipe | here")
    assert commit is None


def test_parse_docs_commit():
    commit = parse_commit_line("vwx9012|2026-07-18T17:00:00+00:00|docs: update installation guide")
    assert commit is not None
    assert commit.type == "docs"


# ──────────────────────────────────────────────────────────────────── #
# group_commits_by_version
# ──────────────────────────────────────────────────────────────────── #
def test_group_no_tags_single_unreleased_section():
    commits = [
        Commit(hash="a1", date="2026-07-18", raw_subject="feat: first", type="feat", description="first"),
        Commit(hash="b2", date="2026-07-17", raw_subject="fix: second", type="fix", description="second"),
    ]
    sections = group_commits_by_version(commits, [])
    assert len(sections) == 1
    assert sections[0].version == "Unreleased"
    assert len(sections[0].commits) == 2


def test_group_with_tags():
    commits = [
        Commit(hash="a1", date="2026-07-20", raw_subject="feat: new", type="feat", description="new"),
        Commit(hash="b2", date="2026-07-15", raw_subject="fix: old", type="fix", description="old"),
    ]
    tags = [("v1.0.0", "2026-07-16")]
    sections = group_commits_by_version(commits, tags)
    assert len(sections) >= 1
    # Latest commit should be in Unreleased (after the tag)
    assert any(s.version == "Unreleased" for s in sections)


def test_group_empty_commits():
    sections = group_commits_by_version([], [])
    assert sections == []


# ──────────────────────────────────────────────────────────────────── #
# generate_markdown
# ──────────────────────────────────────────────────────────────────── #
def test_markdown_has_header():
    sections = [VersionSection(version="Unreleased", date="2026-07-18", commits=[])]
    md = generate_markdown(sections)
    assert "# Changelog" in md
    assert "Keep a Changelog" in md
    assert "Semantic Versioning" in md


def test_markdown_has_version_section():
    commit = Commit(hash="abc1234", date="2026-07-18", raw_subject="feat: test", type="feat", description="test")
    sections = [VersionSection(version="v1.0.0", date="2026-07-18", commits=[commit])]
    md = generate_markdown(sections)
    assert "## [v1.0.0] - 2026-07-18" in md
    assert "✨ Features" in md
    assert "test" in md
    assert "abc1234"[:7] in md


def test_markdown_groups_by_type():
    commits = [
        Commit(hash="a1", date="2026-07-18", raw_subject="feat: add", type="feat", description="add"),
        Commit(hash="b2", date="2026-07-18", raw_subject="fix: repair", type="fix", description="repair"),
        Commit(hash="c3", date="2026-07-18", raw_subject="docs: readme", type="docs", description="readme"),
    ]
    sections = [VersionSection(version="Unreleased", date="2026-07-18", commits=commits)]
    md = generate_markdown(sections)
    assert "✨ Features" in md
    assert "🐛 Bug Fixes" in md
    assert "📚 Documentation" in md


def test_markdown_empty_sections():
    md = generate_markdown([])
    assert "# Changelog" in md
    assert "No commits found" in md


def test_markdown_handles_merge_commits():
    commits = [
        Commit(hash="a1", date="2026-07-18", raw_subject="feat: real", type="feat", description="real"),
        Commit(hash="b2", date="2026-07-18", raw_subject="Merge pull request #1", type="merge", description="Merge pull request #1", is_merge=True),
    ]
    sections = [VersionSection(version="Unreleased", date="2026-07-18", commits=commits)]
    md = generate_markdown(sections)
    assert "feat" in md.lower()
    # Merge commits should NOT appear in the grouped sections
    assert "Merge pull request" not in md


def test_markdown_commit_hash_truncated():
    commit = Commit(hash="abcdefghij1234567890", date="2026-07-18", raw_subject="feat: test", type="feat", description="test")
    sections = [VersionSection(version="Unreleased", date="2026-07-18", commits=[commit])]
    md = generate_markdown(sections)
    assert "abcdefg" in md  # 7-char hash


# ──────────────────────────────────────────────────────────────────── #
# format_commit_entry
# ──────────────────────────────────────────────────────────────────── #
def test_format_commit_with_scope():
    commit = Commit(hash="abc1234", date="2026-07-18", raw_subject="fix(api): test", type="fix", scope="api", description="test")
    entry = format_commit_entry(commit)
    assert "**api:**" in entry
    assert "test" in entry
    assert "abc1234"[:7] in entry


def test_format_commit_without_scope():
    commit = Commit(hash="abc1234", date="2026-07-18", raw_subject="feat: test", type="feat", description="test")
    entry = format_commit_entry(commit)
    assert "test" in entry
    assert "abc1234"[:7] in entry
    assert "**" not in entry  # no scope bold


# ──────────────────────────────────────────────────────────────────── #
# End-to-end (mocked git)
# ──────────────────────────────────────────────────────────────────── #
def test_generate_changelog_with_mock_git():
    mock_output = "abc1234|2026-07-18T10:00:00+00:00|feat: add new feature\ndef5678|2026-07-17T10:00:00+00:00|fix: fix old bug"
    with patch("solutions.issue_1_changelog.generate_changelog.run_git_log", return_value=mock_output):
        with patch("solutions.issue_1_changelog.generate_changelog.get_tags", return_value=[]):
            md = generate_changelog(repo_path=".")
    assert "# Changelog" in md
    assert "add new feature" in md
    assert "fix old bug" in md


def test_generate_changelog_empty_repo():
    with patch("solutions.issue_1_changelog.generate_changelog.run_git_log", return_value=""):
        md = generate_changelog(repo_path=".")
    assert "No commits found" in md


def test_generate_changelog_writes_file(tmp_path):
    mock_output = "abc1234|2026-07-18T10:00:00+00:00|feat: test"
    output_file = str(tmp_path / "CHANGELOG.md")
    with patch("solutions.issue_1_changelog.generate_changelog.run_git_log", return_value=mock_output):
        with patch("solutions.issue_1_changelog.generate_changelog.get_tags", return_value=[]):
            md = generate_changelog(repo_path=".", output_file=output_file)
    assert Path(output_file).exists()
    assert Path(output_file).read_text() == md
