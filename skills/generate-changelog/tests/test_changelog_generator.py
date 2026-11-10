"""
Tests for changelog_generator.py

Run with:  pytest tests/ -v
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Make changelog_generator importable from parent dir
sys.path.insert(0, str(Path(__file__).parent.parent))
from changelog_generator import (
    CONVENTIONAL_RE,
    get_tags,
    parse_log,
    group_by_version,
    render_markdown,
    render_json,
    detect_repo_url,
    LOG_SEP,
    GIT_FORMAT,
)


# ─────────────────────────── Fixtures ────────────────────────────

def git(args, cwd):
    """Helper: run git in a temp repo."""
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture()
def empty_repo(tmp_path):
    """Bare git repo with no commits."""
    git(["init", "-b", "main"], cwd=tmp_path)
    git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    git(["config", "user.name", "Test"], cwd=tmp_path)
    return tmp_path


@pytest.fixture()
def simple_repo(empty_repo):
    """Repo with a few conventional commits and two tags."""
    repo = empty_repo

    def commit(msg, body=""):
        (repo / "file.txt").write_text(msg)
        git(["add", "."], cwd=repo)
        args = ["commit", "-m", msg]
        if body:
            args += ["-m", body]
        git(args, cwd=repo)

    commit("feat: initial feature")
    commit("fix(auth): resolve login bug")
    git(["tag", "v0.1.0"], cwd=repo)

    commit("feat(api): add REST endpoint")
    commit("chore: update dependencies")
    commit("docs: improve README")
    git(["tag", "v0.2.0"], cwd=repo)

    commit("feat!: redesign API", "BREAKING CHANGE: old endpoints removed")
    commit("fix: patch null pointer")

    return repo


@pytest.fixture()
def no_tag_repo(empty_repo):
    """Repo with commits but no tags."""
    repo = empty_repo
    for i in range(3):
        (repo / f"f{i}.txt").write_text(str(i))
        git(["add", "."], cwd=repo)
        git(["commit", "-m", f"feat: feature {i}"], cwd=repo)
    return repo


# ──────────────────── Unit: CONVENTIONAL_RE ──────────────────────

@pytest.mark.parametrize("subject,exp_type,exp_scope,exp_breaking,exp_desc", [
    ("feat: add thing",               "feat",     "",      False, "add thing"),
    ("fix(auth): bug",                "fix",      "auth",  False, "bug"),
    ("feat(api)!: break",             "feat",     "api",   True,  "break"),
    ("chore: bump deps",              "chore",    "",      False, "bump deps"),
    ("FEAT: upper case",              "feat",     "",      False, "upper case"),
    ("refactor(core): clean up code", "refactor", "core",  False, "clean up code"),
])
def test_conventional_re(subject, exp_type, exp_scope, exp_breaking, exp_desc):
    m = CONVENTIONAL_RE.match(subject)
    assert m is not None, f"Pattern did not match: {subject!r}"
    assert m.group("type").lower() == exp_type
    assert (m.group("scope") or "") == exp_scope
    assert bool(m.group("breaking")) == exp_breaking
    assert m.group("description").strip() == exp_desc


def test_conventional_re_no_match():
    assert CONVENTIONAL_RE.match("Just a plain commit message") is None
    assert CONVENTIONAL_RE.match("") is None


# ──────────────────────── Unit: parse_log ────────────────────────

def _make_raw_block(sha="abc1234", sha_short="abc1234", refs="",
                    subject="feat: something", body="", email="a@b.com",
                    date="2024-01-15 10:00:00 +0000"):
    return (
        f"{LOG_SEP}{sha}\n{sha_short}\n{refs}\n{subject}\n{body}\n{email}\n{date}"
    )


def test_parse_log_basic():
    raw = _make_raw_block(subject="feat(ui): add button")
    commits = parse_log(raw)
    assert len(commits) == 1
    c = commits[0]
    assert c["type"] == "feat"
    assert c["scope"] == "ui"
    assert c["desc"] == "add button"
    assert c["breaking"] is False


def test_parse_log_breaking_body():
    raw = _make_raw_block(
        subject="refactor: big change",
        body="BREAKING CHANGE: removed old API",
    )
    commits = parse_log(raw)
    assert commits[0]["breaking"] is True


def test_parse_log_multiple():
    raw = (
        _make_raw_block(subject="fix: bug1") +
        "\n" +
        _make_raw_block(subject="feat: feature2")
    )
    commits = parse_log(raw)
    assert len(commits) == 2


def test_parse_log_non_conventional():
    raw = _make_raw_block(subject="Update README")
    commits = parse_log(raw)
    c = commits[0]
    assert c["type"] == "other"
    assert c["desc"] == "Update README"


def test_parse_log_empty():
    commits = parse_log("")
    assert commits == []


# ───────────────── Integration: get_tags ─────────────────────────

def test_get_tags_empty(no_tag_repo):
    tags = get_tags(str(no_tag_repo))
    assert tags == []


def test_get_tags_ordered(simple_repo):
    tags = get_tags(str(simple_repo))
    tag_names = [t[0] for t in tags]
    # v0.2.0 should come before v0.1.0 (newest first)
    assert tag_names.index("v0.2.0") < tag_names.index("v0.1.0")


# ──────────────── Integration: group_by_version ──────────────────

def test_group_by_version_no_tags(no_tag_repo):
    sections = group_by_version(str(no_tag_repo))
    assert len(sections) == 1
    assert sections[0]["version"] == "Unreleased"
    assert len(sections[0]["commits"]) == 3


def test_group_by_version_with_tags(simple_repo):
    sections = group_by_version(str(simple_repo))
    versions = [s["version"] for s in sections]
    # Should have Unreleased + v0.2.0 + v0.1.0
    assert "Unreleased" in versions
    assert "v0.2.0" in versions
    assert "v0.1.0" in versions


def test_group_by_version_since_tag(simple_repo):
    sections = group_by_version(str(simple_repo), since_tag="v0.2.0")
    versions = [s["version"] for s in sections]
    assert "v0.1.0" not in versions


def test_group_by_version_commit_counts(simple_repo):
    sections = group_by_version(str(simple_repo))
    by_ver = {s["version"]: s for s in sections}
    # v0.1.0 has 2 commits: feat + fix
    assert len(by_ver["v0.1.0"]["commits"]) == 2
    # v0.2.0 has 3 commits: feat + chore + docs
    assert len(by_ver["v0.2.0"]["commits"]) == 3
    # Unreleased has 2: feat! + fix
    assert len(by_ver["Unreleased"]["commits"]) == 2


# ───────────────── Unit: render_markdown ─────────────────────────

def _make_section(version="v1.0.0", date="2024-01-01", commits=None):
    if commits is None:
        from datetime import datetime, timezone
        commits = [{
            "sha_full": "abc" * 13 + "ab",
            "sha_short": "abc1234",
            "type": "feat",
            "scope": "",
            "breaking": False,
            "desc": "awesome feature",
            "body": "",
            "email": "dev@example.com",
            "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
        }]
    return {"version": version, "date": date, "commits": commits}


def test_render_markdown_contains_version():
    md = render_markdown([_make_section("v2.0.0", "2024-06-01")])
    assert "v2.0.0" in md
    assert "2024-06-01" in md


def test_render_markdown_has_header():
    md = render_markdown([_make_section()])
    assert md.startswith("# Changelog")


def test_render_markdown_feat_section():
    md = render_markdown([_make_section()])
    assert "Features" in md
    assert "awesome feature" in md


def test_render_markdown_breaking_section():
    from datetime import datetime, timezone
    commits = [{
        "sha_full": "d" * 40,
        "sha_short": "ddd1234",
        "type": "feat",
        "scope": "api",
        "breaking": True,
        "desc": "remove old API",
        "body": "BREAKING CHANGE: removed /v1",
        "email": "dev@x.com",
        "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }]
    md = render_markdown([{"version": "v3.0.0", "date": "2024-01-01", "commits": commits}])
    assert "Breaking Changes" in md
    assert "remove old API" in md


def test_render_markdown_with_repo_url():
    md = render_markdown(
        [_make_section("v1.0.0", "2024-01-01")],
        repo_url="https://github.com/org/repo",
    )
    assert "https://github.com/org/repo/releases/tag/v1.0.0" in md


def test_render_markdown_empty_sections():
    md = render_markdown([])
    assert "# Changelog" in md


# ──────────────────── Unit: render_json ──────────────────────────

def test_render_json_structure():
    result = json.loads(render_json([_make_section("v1.0.0", "2024-01-01")]))
    assert isinstance(result, list)
    assert result[0]["version"] == "v1.0.0"
    assert isinstance(result[0]["commits"], list)
    commit = result[0]["commits"][0]
    assert "sha" in commit
    assert "type" in commit
    assert "desc" in commit


def test_render_json_multiple_versions():
    sections = [
        _make_section("v2.0.0", "2024-06-01"),
        _make_section("v1.0.0", "2024-01-01"),
    ]
    result = json.loads(render_json(sections))
    assert len(result) == 2
    assert result[0]["version"] == "v2.0.0"


# ───────────── Integration: CLI end-to-end ───────────────────────

def test_cli_markdown_stdout(simple_repo):
    result = subprocess.run(
        [sys.executable, "changelog_generator.py", "--repo", str(simple_repo)],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "# Changelog" in result.stdout
    assert "v0.2.0" in result.stdout


def test_cli_json_format(simple_repo):
    result = subprocess.run(
        [sys.executable, "changelog_generator.py",
         "--repo", str(simple_repo), "--format", "json"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert any(s["version"] == "v0.1.0" for s in data)


def test_cli_output_file(simple_repo, tmp_path):
    out = tmp_path / "CHANGELOG.md"
    result = subprocess.run(
        [sys.executable, "changelog_generator.py",
         "--repo", str(simple_repo), "--output", str(out)],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert out.exists()
    content = out.read_text()
    assert "# Changelog" in content


def test_cli_since_tag(simple_repo):
    result = subprocess.run(
        [sys.executable, "changelog_generator.py",
         "--repo", str(simple_repo), "--since-tag", "v0.2.0"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "v0.1.0" not in result.stdout


def test_cli_no_emoji(simple_repo):
    result = subprocess.run(
        [sys.executable, "changelog_generator.py",
         "--repo", str(simple_repo), "--no-emoji"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # Should not contain emoji sequences
    import re
    assert not re.search(r"[\U0001F300-\U0001FAFF]", result.stdout)


def test_cli_invalid_repo(tmp_path):
    result = subprocess.run(
        [sys.executable, "changelog_generator.py", "--repo", str(tmp_path)],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "not a git repository" in result.stderr
