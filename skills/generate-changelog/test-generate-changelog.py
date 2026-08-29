#!/usr/bin/env python3
"""Unit tests for generate-changelog.py."""
from __future__ import annotations

import unittest
import unittest.mock
from pathlib import Path

# Import the script as a module.
import importlib.util

SPEC = importlib.util.spec_from_file_location(
    "generate_changelog",
    Path(__file__).with_name("generate-changelog.py"),
)
generate_changelog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_changelog)  # type: ignore[union-attr]


class TestParseConventional(unittest.TestCase):
    def test_basic_feat(self):
        self.assertEqual(
            generate_changelog.parse_conventional("feat: add login"),
            ("feat", "add login", False),
        )

    def test_scope(self):
        self.assertEqual(
            generate_changelog.parse_conventional("fix(api): handle null user"),
            ("fix", "handle null user", False),
        )

    def test_breaking_bang(self):
        self.assertEqual(
            generate_changelog.parse_conventional("feat!: drop legacy endpoint"),
            ("feat", "drop legacy endpoint", True),
        )

    def test_non_conventional(self):
        self.assertEqual(
            generate_changelog.parse_conventional("Update readme"),
            ("", "Update readme", False),
        )


class TestCategorize(unittest.TestCase):
    def test_groups(self):
        commits = [
            {"hash": "a", "short": "a", "message": "feat: add feature", "author": "A"},
            {"hash": "b", "short": "b", "message": "fix: bug fix", "author": "B"},
            {"hash": "c", "short": "c", "message": "docs: update readme", "author": "C"},
            {"hash": "d", "short": "d", "message": "chore: cleanup", "author": "D"},
        ]
        sections = generate_changelog.categorize(commits)
        self.assertEqual(len(sections["Added"]), 1)
        self.assertEqual(len(sections["Fixed"]), 1)
        self.assertEqual(len(sections["Documentation"]), 1)
        self.assertEqual(len(sections["Maintenance"]), 1)

    def test_breaking(self):
        commits = [
            {"hash": "x", "short": "x", "message": "feat!: breaking change", "author": "X"},
        ]
        sections = generate_changelog.categorize(commits)
        self.assertEqual(len(sections["Breaking Changes"]), 1)


class TestFormatEntry(unittest.TestCase):
    def test_with_repo_url(self):
        commit = {"hash": "abc123", "short": "abc", "message": "fix bug", "author": "A"}
        entry = generate_changelog.format_entry(commit, "https://github.com/owner/repo")
        self.assertIn("https://github.com/owner/repo/commit/abc123", entry)

    def test_without_repo_url(self):
        commit = {"hash": "abc123", "short": "abc", "message": "fix bug", "author": "A"}
        entry = generate_changelog.format_entry(commit, None)
        self.assertIn("`abc`", entry)


class TestPrependToFile(unittest.TestCase):
    def test_prepends_to_existing(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Changelog\n\n## Old\n")
            path = Path(f.name)
        try:
            generate_changelog.prepend_to_file("## New\n", path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("## New", text)
            self.assertIn("## Old", text)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
