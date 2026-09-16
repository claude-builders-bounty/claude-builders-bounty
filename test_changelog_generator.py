import unittest
from changelog_generator import categorize_commits, generate_markdown_changelog

class TestChangelogGenerator(unittest.TestCase):
    def test_categorize_commits(self):
        mock_commits = [
            {"hash": "a1b2c3d", "message": "feat: add user authentication", "author": "dev", "date": "2026-09-01"},
            {"hash": "e4f5g6h", "message": "fix: resolve memory leak in worker", "author": "dev", "date": "2026-09-02"},
        ]
        cats = categorize_commits(mock_commits)
        self.assertEqual(len(cats["Added"]), 1)
        self.assertEqual(len(cats["Fixed"]), 1)

    def test_generate_markdown(self):
        mock_commits = [
            {"hash": "a1b2c3d", "message": "feat: add user auth", "author": "alice", "date": "2026-09-01"}
        ]
        md = generate_markdown_changelog("1.0.0", mock_commits)
        self.assertIn("## [1.0.0]", md)
        self.assertIn("### Added", md)
        self.assertIn("feat: add user auth", md)

if __name__ == "__main__":
    unittest.main()
