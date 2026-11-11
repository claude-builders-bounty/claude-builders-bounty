#!/usr/bin/env python3
"""
Unit test suite for changelog-generator (Python & Bash)
Verifies categorization, tag detection, and formatting against an isolated Git repository.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PYTHON_SCRIPT = Path(__file__).parent / "changelog.py"

BASH_SCRIPT = Path(__file__).parent / "changelog.sh"


def run_cmd(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)


def init_sample_repo(test_dir, with_tag=True):
    run_cmd(["git", "init"], test_dir)
    run_cmd(["git", "config", "user.name", "Test User"], test_dir)
    run_cmd(["git", "config", "user.email", "test@example.com"], test_dir)

    Path(test_dir, "init.txt").write_text("initial", encoding="utf-8")
    run_cmd(["git", "add", "."], test_dir)
    run_cmd(["git", "commit", "-m", "chore: initial commit"], test_dir)
    if with_tag:
        run_cmd(["git", "tag", "v1.0.0"], test_dir)

    commits = [
        ("feat: add webhook integration", "file1.txt"),
        ("fix(net): resolve connection & timeout issue", "file2.txt"),
        ("refactor: optimize \\pipeline\\ processing", "file3.txt"),
        ("revert: drop obsolete legacy flag", "file4.txt"),
        ("random unformatted commit message", "file5.txt"),
    ]
    for msg, fname in commits:
        Path(test_dir, fname).write_text(msg, encoding="utf-8")
        run_cmd(["git", "add", "."], test_dir)
        run_cmd(["git", "commit", "-m", msg], test_dir)


def assert_expected_sections(content):
    assert "# Changelog" in content, "Missing main # Changelog header"
    assert "### Added" in content, "Missing ### Added section"
    assert "Add webhook integration" in content, "Missing Added commit entry"
    assert "### Fixed" in content, "Missing ### Fixed section"
    assert "Resolve connection & timeout issue" in content, "Missing Fixed commit entry"
    assert "### Changed" in content, "Missing ### Changed section"
    assert "Optimize \\pipeline\\ processing" in content, "Missing Changed commit entry"
    assert "### Removed" in content, "Missing ### Removed section"
    assert "Drop obsolete legacy flag" in content, "Missing Removed commit entry"
    assert "### Other Changes" in content, "Missing Other Changes section"


def test_changelog_generator():
    test_dir = tempfile.mkdtemp(prefix="test_changelog_py_")
    try:
        init_sample_repo(test_dir, with_tag=True)
        shutil.copy(PYTHON_SCRIPT, Path(test_dir, "changelog.py"))
        proc = subprocess.run(["python", "changelog.py"], cwd=test_dir, capture_output=True, text=True)
        assert proc.returncode == 0, f"changelog.py failed with stderr: {proc.stderr}"

        changelog_file = Path(test_dir, "CHANGELOG.md")
        assert changelog_file.exists(), "CHANGELOG.md was not generated!"
        content = changelog_file.read_text(encoding="utf-8")
        assert_expected_sections(content)

        # Verify prepend preserves earlier history without duplicating headers
        Path(test_dir, "file6.txt").write_text("single commit", encoding="utf-8")
        run_cmd(["git", "add", "."], test_dir)
        run_cmd(["git", "commit", "-m", "feat: follow-up feature"], test_dir)
        proc2 = subprocess.run(["python", "changelog.py"], cwd=test_dir, capture_output=True, text=True)
        assert proc2.returncode == 0
        content2 = changelog_file.read_text(encoding="utf-8")
        assert content2.count("# Changelog") == 1
        assert "Follow-up feature" in content2
        assert "Add webhook integration" in content2
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_changelog_bash_single_commit_and_sections():
    bash = shutil.which("bash")
    git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
    if os.name == "nt" and git_bash.exists():
        bash = str(git_bash)
    if not bash:
        return

    test_dir = tempfile.mkdtemp(prefix="test_changelog_sh_")
    try:
        run_cmd(["git", "init"], test_dir)
        run_cmd(["git", "config", "user.name", "Test User"], test_dir)
        run_cmd(["git", "config", "user.email", "test@example.com"], test_dir)
        Path(test_dir, "init.txt").write_text("init", encoding="utf-8")
        run_cmd(["git", "add", "."], test_dir)
        run_cmd(["git", "commit", "-m", "chore: init"], test_dir)
        run_cmd(["git", "tag", "v1.0.0"], test_dir)

        # Regression test: single commit after tag must not be dropped at EOF
        Path(test_dir, "f1.txt").write_text("one", encoding="utf-8")
        run_cmd(["git", "add", "."], test_dir)
        run_cmd(["git", "commit", "-m", "feat: single commit support"], test_dir)

        proc = subprocess.run([bash, str(BASH_SCRIPT)], cwd=test_dir, capture_output=True, text=True)
        assert proc.returncode == 0, f"changelog.sh failed: {proc.stderr}\n{proc.stdout}"
        changelog_file = Path(test_dir, "CHANGELOG.md")
        assert changelog_file.exists(), f"CHANGELOG.md missing; stdout={proc.stdout}"
        assert "Single commit support" in changelog_file.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    test_changelog_generator()
    test_changelog_bash_single_commit_and_sections()
    print("All changelog tests passed!")
