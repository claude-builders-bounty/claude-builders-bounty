import unittest
import importlib.machinery
import importlib.util
import os
import sys

# Load generate-changelog dynamically since it has no .py extension
loader = importlib.machinery.SourceFileLoader(
    "changelog_gen",
    os.path.join(os.path.dirname(__file__), "generate-changelog")
)
spec = importlib.util.spec_from_loader("changelog_gen", loader)
changelog_gen = importlib.util.module_from_spec(spec)
loader.exec_module(changelog_gen)

class TestChangelogGenerator(unittest.TestCase):

    def test_classify_commits_basic(self):
        commits = [
            {"hash": "1a2b3c", "subject": "feat: add support for dynamic config"},
            {"hash": "2b3c4d", "subject": "fix: resolve memory leak on exit"},
            {"hash": "3c4d5e", "subject": "remove: delete unused legacy assets"},
            {"hash": "4d5e6f", "subject": "chore: update dependencies"}
        ]
        
        categories = changelog_gen.classify_commits(commits)
        
        # Verify Added category
        self.assertEqual(len(categories["Added"]), 1)
        self.assertIn("feat: add support for dynamic config (1a2b3c)", categories["Added"])
        
        # Verify Fixed category
        self.assertEqual(len(categories["Fixed"]), 1)
        self.assertIn("fix: resolve memory leak on exit (2b3c4d)", categories["Fixed"])
        
        # Verify Removed category
        self.assertEqual(len(categories["Removed"]), 1)
        self.assertIn("remove: delete unused legacy assets (3c4d5e)", categories["Removed"])
        
        # Verify Changed category
        self.assertEqual(len(categories["Changed"]), 1)
        self.assertIn("chore: update dependencies (4d5e6f)", categories["Changed"])

    def test_classify_commits_case_insensitive_and_alternate(self):
        commits = [
            {"hash": "7a8b9c", "subject": "Added: a new validation flag"},
            {"hash": "8b9c0d", "subject": "FIXED: a syntax parsing error"},
            {"hash": "9c0d1e", "subject": "remove: obsolete scripts"}
        ]
        categories = changelog_gen.classify_commits(commits)
        
        self.assertEqual(len(categories["Added"]), 1)
        self.assertEqual(len(categories["Fixed"]), 1)
        self.assertEqual(len(categories["Removed"]), 1)

    def test_build_changelog_markdown_formatting(self):
        categories = {
            "Added": ["feat: add user login (1a2b)"],
            "Fixed": ["fix: patch security issue (3c4d)"],
            "Removed": [],
            "Changed": ["chore: update lockfile (5e6f)"]
        }
        
        markdown = changelog_gen.build_changelog_markdown(categories, tag="v1.0.0")
        
        self.assertIn("# Changelog", markdown)
        self.assertIn("## [Unreleased (since v1.0.0)]", markdown)
        self.assertIn("### Added\n\n- feat: add user login (1a2b)", markdown)
        self.assertIn("### Fixed\n\n- fix: patch security issue (3c4d)", markdown)
        self.assertIn("### Changed\n\n- chore: update lockfile (5e6f)", markdown)
        self.assertNotIn("### Removed", markdown) # Should be skipped because it is empty

if __name__ == "__main__":
    unittest.main()
