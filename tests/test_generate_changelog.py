import unittest

from scripts.generate_changelog import Commit, categorize, render_changelog


class GenerateChangelogTest(unittest.TestCase):
    def test_categorizes_common_commit_prefixes(self):
        self.assertEqual(categorize("fix login error"), "Fixed")
        self.assertEqual(categorize("remove deprecated API"), "Removed")
        self.assertEqual(categorize("update dashboard copy"), "Changed")
        self.assertEqual(categorize("add billing page"), "Added")

    def test_render_includes_required_sections(self):
        output = render_changelog(
            [
                Commit("abc123", "add billing page"),
                Commit("def456", "fix login error"),
            ],
            tag="v1.0.0",
            version="Unreleased",
        )
        self.assertIn("## Unreleased - ", output)
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Changed", output)
        self.assertIn("### Removed", output)
        self.assertIn("add billing page (abc123)", output)


if __name__ == "__main__":
    unittest.main()
