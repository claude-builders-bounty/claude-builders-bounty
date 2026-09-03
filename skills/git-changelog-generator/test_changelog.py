import unittest
from changelog import categorize_commits, format_markdown

class TestChangelogGenerator(unittest.TestCase):

    def test_conventional_commits_categorization(self):
        sample_commits = [
            "feat(auth): add OAuth2 provider for GitHub",
            "fix(api): resolve null pointer exception in user loader",
            "refactor(db): optimize query performance with compound index",
            "drop(legacy): remove deprecated v1 endpoints",
            "chore: bump dependencies to latest versions",
            "perf: reduce bundle size by 15%"
        ]

        cats = categorize_commits(sample_commits)

        self.assertEqual(len(cats["Added"]), 1)
        self.assertEqual(cats["Added"][0], "Add OAuth2 provider for GitHub")

        self.assertEqual(len(cats["Fixed"]), 1)
        self.assertEqual(cats["Fixed"][0], "Resolve null pointer exception in user loader")

        self.assertEqual(len(cats["Removed"]), 1)
        self.assertEqual(cats["Removed"][0], "Remove deprecated v1 endpoints")

        self.assertEqual(len(cats["Changed"]), 3)

    def test_markdown_formatting(self):
        cats = {
            "Added": ["New dashboard widgets"],
            "Changed": ["Refactored auth middleware"],
            "Fixed": ["Fixed token expiration bug"],
            "Removed": []
        }

        md = format_markdown(cats, tag_name="v1.2.0", date_str="2026-09-03")

        self.assertIn("## [v1.2.0] - 2026-09-03", md)
        self.assertIn("### Added", md)
        self.assertIn("- New dashboard widgets", md)
        self.assertIn("### Changed", md)
        self.assertIn("### Fixed", md)
        self.assertNotIn("### Removed", md)

    def test_fallback_heuristics(self):
        non_conventional = [
            "fixed a critical bug in checkout",
            "added French localization support",
            "deleted old asset files",
            "general cleanup and formatting"
        ]

        cats = categorize_commits(non_conventional)

        self.assertEqual(len(cats["Fixed"]), 1)
        self.assertEqual(len(cats["Added"]), 1)
        self.assertEqual(len(cats["Removed"]), 1)
        self.assertEqual(len(cats["Changed"]), 1)


if __name__ == "__main__":
    unittest.main()
