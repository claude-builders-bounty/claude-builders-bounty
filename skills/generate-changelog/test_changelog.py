import unittest
from generate_changelog import categorize_commit, clean_commit_message, build_changelog_section


class TestChangelogGenerator(unittest.TestCase):
    def test_categorize_conventional_commits(self):
        self.assertEqual(categorize_commit("feat(auth): add OAuth2 provider"), "Added")
        self.assertEqual(categorize_commit("fix: prevent null pointer exception"), "Fixed")
        self.assertEqual(categorize_commit("perf: optimize database query"), "Changed")
        self.assertEqual(categorize_commit("docs: update API documentation"), "Changed")
        self.assertEqual(categorize_commit("chore: bump dependency versions"), "Changed")
        self.assertEqual(categorize_commit("refactor(core): simplify handler loop"), "Changed")
        self.assertEqual(categorize_commit("remove: deprecated legacy endpoints"), "Removed")
        self.assertEqual(categorize_commit("revert: undo accidental release commit"), "Removed")

    def test_categorize_imperative_verbs(self):
        self.assertEqual(categorize_commit("Add dark mode toggle"), "Added")
        self.assertEqual(categorize_commit("Fix broken link in footer"), "Fixed")
        self.assertEqual(categorize_commit("Update README with install instructions"), "Changed")
        self.assertEqual(categorize_commit("Remove unused utility functions"), "Removed")
        self.assertEqual(categorize_commit("Delete obsolete test suite"), "Removed")

    def test_clean_commit_message(self):
        self.assertEqual(
            clean_commit_message("feat(auth): add login endpoint"),
            "Add login endpoint",
        )
        self.assertEqual(
            clean_commit_message("fix: resolve timeout error"),
            "Resolve timeout error",
        )
        self.assertEqual(
            clean_commit_message("docs(guide): improve quickstart steps"),
            "Improve quickstart steps",
        )

    def test_build_changelog_section(self):
        commits = [
            ("abc1234", "feat(cli): add --json output flag", "Alice"),
            ("def5678", "fix: correct exit status code on failure", "Bob"),
            ("789abcd", "docs: document installation steps", "Charlie"),
            ("456ef01", "remove: drop deprecated v1 api", "Dave"),
        ]
        section = build_changelog_section("1.0.0", "2026-11-19", commits)

        self.assertIn("## [1.0.0] - 2026-11-19", section)
        self.assertIn("### Added", section)
        self.assertIn("- Add --json output flag ([`abc1234`])", section)
        self.assertIn("### Fixed", section)
        self.assertIn("- Correct exit status code on failure ([`def5678`])", section)
        self.assertIn("### Changed", section)
        self.assertIn("- Document installation steps ([`789abcd`])", section)
        self.assertIn("### Removed", section)
        self.assertIn("- Drop deprecated v1 api ([`456ef01`])", section)


if __name__ == "__main__":
    unittest.main()
