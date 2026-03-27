import unittest
from src.main import parse_commit

class TestCommitParser(unittest.TestCase):
    def test_conventional_commit_with_scope(self):
        typ, desc = parse_commit("feat(ui): add new dark mode")
        self.assertEqual(typ, "feat")
        self.assertEqual(desc, "add new dark mode")

    def test_conventional_commit_without_scope(self):
        typ, desc = parse_commit("fix: resolve memory leak")
        self.assertEqual(typ, "fix")
        self.assertEqual(desc, "resolve memory leak")

    def test_breaking_change(self):
        typ, desc = parse_commit("feat!: breaking change description")
        self.assertEqual(typ, "feat")
        self.assertEqual(desc, "breaking change description")

    def test_misc_commit(self):
        typ, desc = parse_commit("just a random commit")
        self.assertEqual(typ, "misc")
        self.assertEqual(desc, "just a random commit")

if __name__ == "__main__":
    unittest.main()
