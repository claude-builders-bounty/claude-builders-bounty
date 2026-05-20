#!/usr/bin/env python3
"""Focused tests for the changelog generator."""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("generate_changelog.py")
SPEC = importlib.util.spec_from_file_location("generate_changelog", MODULE_PATH)
assert SPEC and SPEC.loader
generate_changelog = importlib.util.module_from_spec(SPEC)
sys.modules["generate_changelog"] = generate_changelog
SPEC.loader.exec_module(generate_changelog)


class GenerateChangelogTests(unittest.TestCase):
    def test_categorizes_conventional_commits(self) -> None:
        cases = {
            "feat(parser): support scopes": "Added",
            "fix: handle empty git log": "Fixed",
            "docs: update setup guide": "Changed",
            "remove deprecated option": "Removed",
        }

        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(generate_changelog.categorize(subject), expected)

    def test_clean_subject_removes_conventional_prefix(self) -> None:
        self.assertEqual(
            generate_changelog.clean_subject("feat(cli): add dry run mode"),
            "Add dry run mode",
        )

    def test_render_includes_sections_and_commit_entries(self) -> None:
        commits = [
            generate_changelog.Commit("abc123456789", "feat: add parser", ""),
            generate_changelog.Commit("def987654321", "fix: handle empty logs", ""),
            generate_changelog.Commit("987654321abc", "remove legacy flag", ""),
        ]

        output = generate_changelog.render_changelog(
            repo=Path(__file__).resolve().parent,
            commits=commits,
            since_ref="v1.0.0",
            version="v1.1.0",
        )

        self.assertIn(f"## v1.1.0 - {dt.date.today().isoformat()}", output)
        self.assertIn("### Added", output)
        self.assertIn("- Add parser (abc1234)", output)
        self.assertIn("### Fixed", output)
        self.assertIn("- Handle empty logs (def9876)", output)
        self.assertIn("### Removed", output)
        self.assertIn("- Remove legacy flag (9876543)", output)


if __name__ == "__main__":
    unittest.main()
