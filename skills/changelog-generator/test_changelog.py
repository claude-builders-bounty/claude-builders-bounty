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

def run_cmd(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)

def test_changelog_generator():
    test_dir = tempfile.mkdtemp(prefix="test_changelog_")
    try:
        # Initialize isolated git repo
        run_cmd(["git", "init"], test_dir)
        run_cmd(["git", "config", "user.name", "Test User"], test_dir)
        run_cmd(["git", "config", "user.email", "test@example.com"], test_dir)

        # Initial commit & tag v1.0.0
        Path(test_dir, "init.txt").write_text("initial")
        run_cmd(["git", "add", "."], test_dir)
        run_cmd(["git", "commit", "-m", "chore: initial commit"], test_dir)
        run_cmd(["git", "tag", "v1.0.0"], test_dir)

        # Commits for the new release
        commits = [
            ("feat: add webhook integration", "file1.txt"),
            ("fix: resolve connection timeout issue", "file2.txt"),
            ("refactor: optimize data processing pipeline", "file3.txt"),
            ("revert: drop obsolete legacy flag", "file4.txt"),
            ("random unformatted commit message", "file5.txt"),
        ]

        for msg, fname in commits:
            Path(test_dir, fname).write_text(msg)
            run_cmd(["git", "add", "."], test_dir)
            run_cmd(["git", "commit", "-m", msg], test_dir)

        # Copy changelog.py to test dir and execute
        shutil.copy(PYTHON_SCRIPT, Path(test_dir, "changelog.py"))
        proc = subprocess.run(["python", "changelog.py"], cwd=test_dir, capture_output=True, text=True)
        assert proc.returncode == 0, f"changelog.py failed with stderr: {proc.stderr}"

        # Verify CHANGELOG.md
        changelog_file = Path(test_dir, "CHANGELOG.md")
        assert changelog_file.exists(), "CHANGELOG.md was not generated!"
        content = changelog_file.read_text(encoding="utf-8")

        print("Generated CHANGELOG:")
        print(content)

        assert "# Changelog" in content, "Missing main # Changelog header"
        assert "### Added" in content, "Missing ### Added section"
        assert "Add webhook integration" in content, "Missing Added commit entry"
        assert "### Fixed" in content, "Missing ### Fixed section"
        assert "Resolve connection timeout issue" in content, "Missing Fixed commit entry"
        assert "### Changed" in content, "Missing ### Changed section"
        assert "Optimize data processing pipeline" in content, "Missing Changed commit entry"
        assert "### Removed" in content, "Missing ### Removed section"
        assert "Drop obsolete legacy flag" in content, "Missing Removed commit entry"
        assert "### Other Changes" in content, "Missing Other Changes section"

        print("\n🎉 All changelog generator test assertions PASSED!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_changelog_generator()
