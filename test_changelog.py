import unittest
from generate_changelog import categorize_commit

class TestChangelog(unittest.TestCase):
    def test_feat_added(self):
        cat, desc = categorize_commit("feat(auth): add OAuth2 Google login")
        self.assertEqual(cat, "Added")
        self.assertEqual(desc, "**auth**: add OAuth2 Google login")

    def test_fix_fixed(self):
        cat, desc = categorize_commit("fix(api): resolve race condition in token refresh")
        self.assertEqual(cat, "Fixed")
        self.assertEqual(desc, "**api**: resolve race condition in token refresh")

    def test_refactor_changed(self):
        cat, desc = categorize_commit("refactor(db): migrate to Drizzle ORM")
        self.assertEqual(cat, "Changed")

    def test_remove_removed(self):
        cat, desc = categorize_commit("remove: legacy session cookie endpoints")
        self.assertEqual(cat, "Removed")

if __name__ == '__main__':
    unittest.main()
