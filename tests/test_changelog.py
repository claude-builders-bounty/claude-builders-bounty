import unittest
from scripts.changelog import categorize_commits, build_changelog_section

class TestChangelogGenerator(unittest.TestCase):
    def test_categorization_conventional_commits(self):
        sample_commits = [
            ("feat: add user authentication via OAuth", "a1b2c3d", "Alice"),
            ("fix: resolve null pointer on empty database query", "e4f5a6b", "Bob"),
            ("refactor: optimize SQL connection pooling", "c7d8e9f", "Charlie"),
            ("remove: drop deprecated v1 legacy API", "1a2b3c4", "Dana"),
            ("chore: update build dependencies", "5e6f7a8", "Eve"),
        ]
        categorized = categorize_commits(sample_commits)

        self.assertEqual(len(categorized["Added"]), 1)
        self.assertIn("add user authentication via OAuth", categorized["Added"][0])

        self.assertEqual(len(categorized["Fixed"]), 1)
        self.assertIn("resolve null pointer on empty database query", categorized["Fixed"][0])

        self.assertEqual(len(categorized["Changed"]), 2)
        self.assertIn("optimize SQL connection pooling", categorized["Changed"][0])

        self.assertEqual(len(categorized["Removed"]), 1)
        self.assertIn("drop deprecated v1 legacy API", categorized["Removed"][0])

    def test_build_markdown_section(self):
        categorized = {
            "Added": ["- feature A (`abc` by User)"],
            "Fixed": ["- bug fix B (`def` by User)"],
            "Changed": [],
            "Removed": []
        }
        section = build_changelog_section(categorized, tag="v1.0.0", date_str="2026-10-23")
        self.assertIn("## [Unreleased] - 2026-10-23 (since v1.0.0)", section)
        self.assertIn("### Added", section)
        self.assertIn("feature A", section)
        self.assertIn("### Fixed", section)
        self.assertNotIn("### Changed", section)
        self.assertNotIn("### Removed", section)

if __name__ == "__main__":
    unittest.main()
