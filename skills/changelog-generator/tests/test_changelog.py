"""
tests/test_changelog.py
========================
Unit tests for generate_changelog.py commit categorization and Markdown formatting.
"""
import unittest
import sys
from pathlib import Path

# Ensure generate_changelog can be imported regardless of execution working directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_changelog import categorize_commit, clean_commit_message, generate_markdown


class TestChangelogGenerator(unittest.TestCase):

    def test_categorize_commit_added(self):
        self.assertEqual(categorize_commit("feat: add user authentication"), "Added")
        self.assertEqual(categorize_commit("add: new payment gateway"), "Added")
        self.assertEqual(categorize_commit("Added new export button"), "Added")

    def test_categorize_commit_fixed(self):
        self.assertEqual(categorize_commit("fix: resolve memory leak in worker"), "Fixed")
        self.assertEqual(categorize_commit("bug: fix crash on null response"), "Fixed")
        self.assertEqual(categorize_commit("Fixed login timeout bug"), "Fixed")

    def test_categorize_commit_removed(self):
        self.assertEqual(categorize_commit("remove: legacy API v1 endpoints"), "Removed")
        self.assertEqual(categorize_commit("deprecate: old token parser"), "Removed")

    def test_categorize_commit_changed(self):
        self.assertEqual(categorize_commit("refactor: simplify database connection pool"), "Changed")
        self.assertEqual(categorize_commit("chore: update dependencies"), "Changed")
        self.assertEqual(categorize_commit("docs: update setup guide"), "Changed")

    def test_clean_commit_message(self):
        self.assertEqual(clean_commit_message("feat: add user auth"), "Add user auth")
        self.assertEqual(clean_commit_message("fix(auth): resolve null token issue"), "Resolve null token issue")

    def test_generate_markdown_structure(self):
        commits = [
            ("abc1234", "Developer A", "feat: add dark mode theme"),
            ("def5678", "Developer B", "fix: resolve crash on refresh"),
        ]
        md = generate_markdown(commits, version_tag="v1.0.0")
        self.assertIn("# Changelog", md)
        self.assertIn("## [v1.0.0]", md)
        self.assertIn("### Added", md)
        self.assertIn("Add dark mode theme", md)
        self.assertIn("### Fixed", md)
        self.assertIn("Resolve crash on refresh", md)


if __name__ == "__main__":
    unittest.main()
