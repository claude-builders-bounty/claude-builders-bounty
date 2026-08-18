import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from changelog import categorize_commits, format_changelog

class TestChangelogGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_commits = [
            {"subject": "feat: add user authentication flow", "hash": "a1b2c3d", "author": "dev", "date": "2026-08-18"},
            {"subject": "fix: resolve memory leak in worker loop", "hash": "e5f6g7h", "author": "dev", "date": "2026-08-18"},
            {"subject": "refactor: optimize database query index", "hash": "i9j0k1l", "author": "dev", "date": "2026-08-18"},
            {"subject": "remove deprecated v1 endpoint", "hash": "m2n3o4p", "author": "dev", "date": "2026-08-18"}
        ]

    def test_categorize_commits(self):
        cat = categorize_commits(self.mock_commits)
        self.assertEqual(len(cat["Added"]), 1)
        self.assertEqual(len(cat["Fixed"]), 1)
        self.assertEqual(len(cat["Changed"]), 1)
        self.assertEqual(len(cat["Removed"]), 1)

    def test_format_changelog_markdown(self):
        cat = categorize_commits(self.mock_commits)
        md = format_changelog(cat, "1.0.0")
        self.assertIn("# Changelog", md)
        self.assertIn("## [1.0.0]", md)
        self.assertIn("### Added", md)
        self.assertIn("### Fixed", md)
        self.assertIn("### Changed", md)
        self.assertIn("### Removed", md)

if __name__ == "__main__":
    unittest.main()
