#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "generate-changelog.py"
sys.path.insert(0, str(SCRIPT.parent))

import importlib.util

module_spec = importlib.util.spec_from_file_location("generate_changelog", SCRIPT)
generate_changelog = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = generate_changelog
module_spec.loader.exec_module(generate_changelog)


def git(repository: str, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", repository, *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def make_repository() -> str:
    repository = tempfile.mkdtemp()
    git(repository, "init", "--initial-branch=main")
    git(repository, "config", "user.name", "Test User")
    git(repository, "config", "user.email", "test@example.com")
    Path(repository, "README.md").write_text("initial\n", encoding="utf-8")
    git(repository, "add", "README.md")
    git(repository, "commit", "-m", "chore: establish baseline")
    git(repository, "tag", "v1.0.0")

    files_and_subjects = (
        ("signup.py", "feat: add email signup API", "content"),
        ("signup.py", "fix signup timeout on slow networks", "fixed"),
        ("README.md", "docs: update setup instructions", "updated"),
        ("legacy.py", "remove deprecated authentication helper", "obsolete"),
    )
    for filename, subject, contents in files_and_subjects:
        Path(repository, filename).write_text(contents, encoding="utf-8")
        git(repository, "add", filename)
        git(repository, "commit", "-m", subject)
    return repository


class GenerateChangelogTests(unittest.TestCase):
    def test_commits_since_last_tag_are_categorized(self) -> None:
        repository = make_repository()
        changelog = generate_changelog.generate_changelog(
            repository,
            generated_date=date(2026, 10, 27),
        )
        self.assertIn("## v1.0.0 - 2026-10-27", changelog)
        self.assertIn("### Added", changelog)
        self.assertIn("- feat: add email signup API", changelog)
        self.assertIn("### Fixed", changelog)
        self.assertIn("- fix signup timeout on slow networks", changelog)
        self.assertIn("### Changed", changelog)
        self.assertIn("- docs: update setup instructions", changelog)
        self.assertIn("### Removed", changelog)
        self.assertIn("- remove deprecated authentication helper", changelog)

    def test_repository_without_tags_uses_unreleased(self) -> None:
        repository = tempfile.mkdtemp()
        git(repository, "init", "--initial-branch=main")
        git(repository, "config", "user.name", "Test User")
        git(repository, "config", "user.email", "test@example.com")
        Path(repository, "README.md").write_text("hello\n", encoding="utf-8")
        git(repository, "add", "README.md")
        git(repository, "commit", "-m", "feat: create project")
        changelog = generate_changelog.generate_changelog(
            repository,
            generated_date=date(2026, 10, 27),
        )
        self.assertIn("## Unreleased - 2026-10-27", changelog)
        self.assertIn("### Added", changelog)

    def test_no_untagged_commits_is_handled(self) -> None:
        repository = make_repository()
        changelog = generate_changelog.generate_changelog(
            repository,
            generated_date=date(2026, 10, 27),
            tag="HEAD",
        )
        self.assertIn("No untagged commits found.", changelog)


if __name__ == "__main__":
    unittest.main()
