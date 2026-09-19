import pytest
import os
import tempfile
import subprocess
from scripts.generate_changelog import Commit, ChangelogBuilder, generate_changelog, GitRepo

def test_commit_categorization_conventional():
    c_feat = Commit("hash123456", "Alice", "2026-09-19", "feat(auth): add OAuth2 provider support")
    assert c_feat.categorize() == "Added"
    assert c_feat.clean_subject() == "Add OAuth2 provider support"
    assert c_feat.short_hash == "hash123"

    c_fix = Commit("hash223456", "Bob", "2026-09-19", "fix(db): resolve connection pool leak on timeout")
    assert c_fix.categorize() == "Fixed"
    assert c_fix.clean_subject() == "Resolve connection pool leak on timeout"

    c_perf = Commit("hash323456", "Charlie", "2026-09-19", "perf(query): optimize index scans")
    assert c_perf.categorize() == "Changed"

    c_docs = Commit("hash423456", "Dave", "2026-09-19", "docs: update API documentation")
    assert c_docs.categorize() == "Changed"

    c_rem = Commit("hash523456", "Eve", "2026-09-19", "remove: drop deprecated v1 endpoints")
    assert c_rem.categorize() == "Removed"

def test_commit_categorization_freeform_keywords():
    c_add = Commit("h111", "Alice", "2026-09-19", "Implement Solana Blink webhook listener")
    assert c_add.categorize() == "Added" or c_add.categorize() == "Changed"

    c_fix = Commit("h222", "Bob", "2026-09-19", "Fix memory leak in background worker")
    assert c_fix.categorize() == "Fixed"

    c_drop = Commit("h333", "Carol", "2026-09-19", "Delete legacy config parser")
    assert c_drop.categorize() == "Removed"

def test_changelog_builder_markdown():
    commits = [
        Commit("abc1234567", "Dev1", "2026-09-19", "feat: new payment gateway"),
        Commit("def2345678", "Dev2", "2026-09-19", "fix: transaction retry backoff"),
    ]
    builder = ChangelogBuilder(version_name="v2.0.0", release_date="2026-09-19")
    md = builder.build_markdown(commits, prev_tag="v1.0.0")

    assert "## [v2.0.0] - 2026-09-19" in md
    assert "Changes since `v1.0.0` (2 commits)" in md
    assert "### Added" in md
    assert "New payment gateway ([`abc1234`])" in md
    assert "### Fixed" in md
    assert "Transaction retry backoff ([`def2345`])" in md

def test_generate_changelog_file_and_prepend(tmp_path):
    # Initialize a temporary git repository
    repo_dir = str(tmp_path)
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=repo_dir, check=True)

    # First commit
    dummy = tmp_path / "file.txt"
    dummy.write_text("v1")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "feat: initial commit with basic functionality"], cwd=repo_dir, check=True)
    subprocess.run(["git", "tag", "v1.0.0"], cwd=repo_dir, check=True)

    # Second commit after tag
    dummy.write_text("v2")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "fix: handle edge case in parser"], cwd=repo_dir, check=True)

    # Generate changelog
    out_file = "CHANGELOG.md"
    result = generate_changelog(repo_dir=repo_dir, version="v1.1.0", output_file=out_file)

    cl_path = tmp_path / out_file
    assert cl_path.exists()
    content = cl_path.read_text(encoding="utf-8")

    assert "# Changelog" in content
    assert "## [v1.1.0]" in content
    assert "Changes since `v1.0.0`" in content
    assert "### Fixed" in content
    assert "Handle edge case in parser" in content
