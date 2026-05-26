import unittest

from generate_changelog import Commit, build_changelog, categorize


class GenerateChangelogTests(unittest.TestCase):
    def test_categorizes_conventional_commits(self):
        self.assertEqual(categorize("feat: add export button"), "Added")
        self.assertEqual(categorize("fix(parser): handle empty log"), "Fixed")
        self.assertEqual(categorize("remove deprecated flag"), "Removed")
        self.assertEqual(categorize("docs: update README"), "Changed")

    def test_builds_all_required_sections(self):
        output = build_changelog(
            [
                Commit("feat: add export button", "abc1234"),
                Commit("fix: handle empty log", "def5678"),
                Commit("drop legacy option", "aaa1111"),
                Commit("docs: update README", "bbb2222"),
            ],
            "v1.0.0",
        )

        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Changed", output)
        self.assertIn("### Removed", output)
        self.assertIn("- add export button (abc1234)", output)
        self.assertIn("- handle empty log (def5678)", output)


if __name__ == "__main__":
    unittest.main()
