import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_changelog import categorize_commit, build_changelog_section


class TestChangelogGenerator(unittest.TestCase):
    def test_categorize_conventional_commits(self):
        cat, desc = categorize_commit("feat(auth): add OAuth2 Google provider")
        self.assertEqual(cat, "Added")
        self.assertIn("OAuth2 Google provider", desc)

        cat, desc = categorize_commit("fix(api): correct parsing of duration days")
        self.assertEqual(cat, "Fixed")
        self.assertIn("Correct parsing", desc)

        cat, desc = categorize_commit("security(deps): patch lodash vulnerability")
        self.assertEqual(cat, "Security")
        self.assertIn("Patch lodash", desc)

        cat, desc = categorize_commit("remove: legacy v1 endpoints")
        self.assertEqual(cat, "Removed")

        cat, desc = categorize_commit("refactor: simplify database connection pool")
        self.assertEqual(cat, "Changed")

    def test_categorize_fallback_keywords(self):
        cat, desc = categorize_commit("Fixed race condition during initialization")
        self.assertEqual(cat, "Fixed")

        cat, desc = categorize_commit("Added export to CSV option")
        self.assertEqual(cat, "Added")

    def test_build_changelog_section(self):
        sample_commits = [
            ("a1b2c3d", "Alice", "feat(ui): add dark mode toggle"),
            ("e5f6g7h", "Bob", "fix: prevent memory leak in worker thread"),
            ("i9j0k1l", "Charlie", "security: enforce JWT expiration check"),
        ]
        output = build_changelog_section("1.1.0", "2026-11-08", sample_commits)
        self.assertIn("## [1.1.0] - 2026-11-08", output)
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Security", output)
        self.assertIn("`a1b2c3d`", output)


if __name__ == "__main__":
    unittest.main()
