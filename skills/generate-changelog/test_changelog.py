import unittest
from generate_changelog import categorize_commit, generate_markdown

class TestChangelogGenerator(unittest.TestCase):
    def test_conventional_commits(self):
        cat, clean = categorize_commit("feat(auth): add OAuth2 Google login")
        self.assertEqual(cat, "Added")
        self.assertIn("Add OAuth2 Google login", clean)

        cat, clean = categorize_commit("fix(api): resolve 500 error on empty body")
        self.assertEqual(cat, "Fixed")
        self.assertIn("Resolve 500 error on empty body", clean)

        cat, clean = categorize_commit("perf(db): optimize query indexing")
        self.assertEqual(cat, "Changed")
        self.assertIn("Optimize query indexing", clean)

        cat, clean = categorize_commit("remove(legacy): delete deprecated v1 routes")
        self.assertEqual(cat, "Removed")
        self.assertIn("Delete deprecated v1 routes", clean)

    def test_semantic_freeform_commits(self):
        cat, _ = categorize_commit("Add dark mode toggle")
        self.assertEqual(cat, "Added")

        cat, _ = categorize_commit("Patch security flaw in token parser")
        self.assertEqual(cat, "Fixed")

        cat, _ = categorize_commit("Update documentation for SDK")
        self.assertEqual(cat, "Changed")

        cat, _ = categorize_commit("Deprecate old config format")
        self.assertEqual(cat, "Removed")

    def test_markdown_generation(self):
        commits = [
            {"hash": "123456789", "short_hash": "1234567", "author": "alice", "subject": "feat: add webhook support"},
            {"hash": "abcdef123", "short_hash": "abcdef1", "author": "bob", "subject": "fix: race condition in queue"}
        ]
        md = generate_markdown(commits, version="v1.0.0", since_tag="v0.9.0")
        self.assertIn("## [v1.0.0]", md)
        self.assertIn("### Added", md)
        self.assertIn("### Fixed", md)
        self.assertIn("@alice", md)
        self.assertIn("@bob", md)

if __name__ == "__main__":
    unittest.main()
