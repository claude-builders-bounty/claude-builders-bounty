import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import unittest
from unittest.mock import patch
from generate_changelog import categorize_commits, format_changelog_section, generate_changelog

class TestChangelogGenerator(unittest.TestCase):

    def test_categorize_commits_conventional(self):
        sample_commits = [
            ("a1b2c3d", "Alice", "2026-09-01", "feat(auth): add OAuth2 provider login"),
            ("d4e5f6a", "Bob", "2026-09-01", "fix: prevent token leak in headers"),
            ("b7c8d9e", "Charlie", "2026-08-31", "chore(deps): update fast-jwt to 4.2.0"),
            ("f1a2b3c", "Dana", "2026-08-30", "remove(legacy): delete deprecated v1 endpoints"),
            ("c3d4e5f", "Evan", "2026-08-29", "docs: update API setup guide")
        ]

        categorized = categorize_commits(sample_commits)

        self.assertEqual(len(categorized["Added"]), 1)
        self.assertEqual(categorized["Added"][0][0], "Add OAuth2 provider login")
        self.assertEqual(categorized["Added"][0][1], "a1b2c3d")

        self.assertEqual(len(categorized["Fixed"]), 1)
        self.assertEqual(categorized["Fixed"][0][0], "Prevent token leak in headers")

        self.assertEqual(len(categorized["Removed"]), 1)
        self.assertEqual(categorized["Removed"][0][0], "Delete deprecated v1 endpoints")

        self.assertEqual(len(categorized["Changed"]), 2)

    def test_format_changelog_section(self):
        categorized = {
            "Added": [("Support SQLite WAL mode", "1234567", "Dev")],
            "Fixed": [("Resolve connection timeout", "890abcd", "Engineer")],
            "Changed": [],
            "Removed": []
        }

        section = format_changelog_section("1.1.0", "2026-09-01", categorized)
        self.assertIn("## [1.1.0] - 2026-09-01", section)
        self.assertIn("### Added", section)
        self.assertIn("- Support SQLite WAL mode ([`1234567`]) - *Dev*", section)
        self.assertIn("### Fixed", section)
        self.assertIn("- Resolve connection timeout ([`890abcd`]) - *Engineer*", section)
        self.assertNotIn("### Changed", section)

    @patch("generate_changelog.get_git_commits")
    @patch("generate_changelog.get_latest_git_tag")
    def test_generate_changelog_content(self, mock_tag, mock_commits):
        mock_tag.return_value = "v1.0.0"
        mock_commits.return_value = [
            ("abcdef1", "Dev", "2026-09-01", "feat: implement autonomous solver"),
            ("abcdef2", "Dev", "2026-09-01", "fix: handle edge case timeout")
        ]

        content = generate_changelog(version="v1.1.0")
        self.assertIn("# Changelog", content)
        self.assertIn("## [v1.1.0]", content)
        self.assertIn("Implement autonomous solver", content)
        self.assertIn("Handle edge case timeout", content)

if __name__ == "__main__":
    unittest.main()
