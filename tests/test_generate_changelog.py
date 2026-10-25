import unittest
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_changelog import categorize_commits, build_markdown_section


class TestChangelogGenerator(unittest.TestCase):

    def test_categorize_conventional_commits(self):
        sample_commits = [
            ("a1b2c3d", "feat(auth): add OAuth2 provider support", "Alice"),
            ("e5f6g7h", "fix(db): resolve connection pool leak on timeout", "Bob"),
            ("i9j0k1l", "chore: upgrade dependencies", "Charlie"),
            ("m2n3o4p", "revert: drop deprecated v1 endpoints", "Diana"),
            ("q5r6s7t", "docs: update API reference documentation", "Eve"),
        ]

        cats = categorize_commits(sample_commits)

        self.assertEqual(len(cats["Added"]), 1)
        self.assertIn("add OAuth2 provider support", cats["Added"][0])

        self.assertEqual(len(cats["Fixed"]), 1)
        self.assertIn("resolve connection pool leak", cats["Fixed"][0])

        self.assertEqual(len(cats["Changed"]), 2)
        self.assertEqual(len(cats["Removed"]), 1)

    def test_markdown_formatting(self):
        cats = {
            "Added": ["- New feature A ([`1234567`] - Alice)"],
            "Fixed": ["- Fixed crash B ([`abcdef0`] - Bob)"],
            "Changed": [],
            "Removed": []
        }
        md = build_markdown_section("v1.2.0", cats, date_str="2026-10-25")
        self.assertIn("## [v1.2.0] - 2026-10-25", md)
        self.assertIn("### Added", md)
        self.assertIn("### Fixed", md)
        self.assertNotIn("### Changed", md)
        self.assertNotIn("### Removed", md)


if __name__ == "__main__":
    unittest.main()
