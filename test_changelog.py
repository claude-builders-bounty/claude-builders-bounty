import unittest
from changelog import categorize_commit, generate_markdown

class TestChangelog(unittest.TestCase):
    def test_categorize_feat(self):
        cat, desc = categorize_commit("feat(auth): add OAuth2 provider support")
        self.assertEqual(cat, "Added")
        self.assertEqual(desc, "add OAuth2 provider support")

    def test_categorize_fix(self):
        cat, desc = categorize_commit("fix: resolve null pointer in user session")
        self.assertEqual(cat, "Fixed")
        self.assertEqual(desc, "resolve null pointer in user session")

    def test_categorize_refactor(self):
        cat, desc = categorize_commit("refactor(core): optimize AST token parser")
        self.assertEqual(cat, "Changed")

    def test_markdown_generation(self):
        commits = [
            {"hash": "abc1234", "subject": "feat: add webhook integration", "author": "Alice", "date": "2026-08-18"},
            {"hash": "def5678", "subject": "fix: patch memory leak", "author": "Bob", "date": "2026-08-18"}
        ]
        md = generate_markdown("v1.0.0", commits)
        self.assertIn("### Added", md)
        self.assertIn("### Fixed", md)
        self.assertIn("add webhook integration", md)
        self.assertIn("patch memory leak", md)

if __name__ == '__main__':
    unittest.main()
