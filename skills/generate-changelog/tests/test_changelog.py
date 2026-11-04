import unittest
import sys
from pathlib import Path

# Add directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from generate_changelog import categorize_commit, build_changelog

class TestChangelogCategorization(unittest.TestCase):

    def test_01_added_feature_prefix(self):
        cat, msg = categorize_commit("feat(auth): add OAuth2 provider support")
        self.assertEqual(cat, "Added")
        self.assertIn("OAuth2 provider support", msg)

    def test_02_added_plain_prefix(self):
        cat, msg = categorize_commit("add: support for custom webhooks")
        self.assertEqual(cat, "Added")
        self.assertIn("support for custom webhooks", msg)

    def test_03_fixed_bug_prefix(self):
        cat, msg = categorize_commit("fix(router): prevent 404 on trailing slash")
        self.assertEqual(cat, "Fixed")
        self.assertIn("prevent 404 on trailing slash", msg)

    def test_04_fixed_plain_prefix(self):
        cat, msg = categorize_commit("resolve: memory leak in worker pool")
        self.assertEqual(cat, "Fixed")
        self.assertIn("memory leak in worker pool", msg)

    def test_05_changed_refactor_prefix(self):
        cat, msg = categorize_commit("refactor(storage): simplify s3 bucket wrapper")
        self.assertEqual(cat, "Changed")
        self.assertIn("simplify s3 bucket wrapper", msg)

    def test_06_changed_chore_prefix(self):
        cat, msg = categorize_commit("chore(deps): update httpx to 0.28.0")
        self.assertEqual(cat, "Changed")
        self.assertIn("update httpx to 0.28.0", msg)

    def test_07_removed_revert_prefix(self):
        cat, msg = categorize_commit("remove: drop deprecated legacy api v1")
        self.assertEqual(cat, "Removed")
        self.assertIn("drop deprecated legacy api v1", msg)

    def test_08_removed_revert_git_style(self):
        cat, msg = categorize_commit("revert: restore previous session handler")
        self.assertEqual(cat, "Removed")
        self.assertIn("restore previous session handler", msg)

    def test_09_build_changelog_formatting(self):
        mock_commits = [
            "a1b2c3d|Alice|2026-11-04|feat(core): implement changelog parser",
            "e4f5g6h|Bob|2026-11-04|fix(parser): handle empty git tags properly",
            "i7j8k9l|Charlie|2026-11-04|chore: update documentation"
        ]
        res = build_changelog(version="1.0.0", since_tag="v0.9.0", commits=mock_commits)
        self.assertIn("## [1.0.0]", res)
        self.assertIn("### Added", res)
        self.assertIn("### Fixed", res)
        self.assertIn("### Changed", res)
        self.assertIn("`a1b2c3d`", res)

    def test_10_empty_commits_fallback(self):
        res = build_changelog(version="1.0.0", since_tag=None, commits=[])
        self.assertIn("No commits found", res)

if __name__ == "__main__":
    unittest.main()
