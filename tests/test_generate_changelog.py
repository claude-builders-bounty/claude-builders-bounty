"""
Unit tests for git changelog generator (Bounty #1).
Zero external dependencies.
"""

import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "generate-changelog"))

from generate_changelog import categorize_commits, render_changelog_markdown


class TestGenerateChangelog(unittest.TestCase):
    def test_categorize_commits(self):
        sample_commits = [
            "a1b2c3d|feat: add user authentication",
            "e4f5g6h|fix: resolve race condition in token refresh",
            "7890abc|refactor: simplify database connection pool",
            "def1234|docs: update API documentation",
            "56789ab|remove: deprecated legacy endpoints",
            "cdef012|sec: sanitize user input against XSS",
            "1122334|chore: bump dependencies",
        ]

        categories = categorize_commits(sample_commits)

        self.assertEqual(len(categories["Added"]), 1)
        self.assertIn("feat: add user authentication", categories["Added"][0])

        self.assertEqual(len(categories["Fixed"]), 1)
        self.assertIn("fix: resolve race condition", categories["Fixed"][0])

        self.assertEqual(len(categories["Changed"]), 1)
        self.assertIn("refactor: simplify database connection pool", categories["Changed"][0])

        self.assertEqual(len(categories["Documentation"]), 1)
        self.assertIn("docs: update API documentation", categories["Documentation"][0])

        self.assertEqual(len(categories["Removed"]), 1)
        self.assertIn("remove: deprecated legacy endpoints", categories["Removed"][0])

        self.assertEqual(len(categories["Security"]), 1)
        self.assertIn("sec: sanitize user input against XSS", categories["Security"][0])

        self.assertEqual(len(categories["Other"]), 1)
        self.assertIn("chore: bump dependencies", categories["Other"][0])

    def test_render_changelog_markdown(self):
        categories = {
            "Added": ["- feat: new dashboard view (`1234567`)"],
            "Fixed": ["- fix: button overflow on mobile (`89abcdef`)"],
            "Changed": [],
            "Removed": [],
            "Security": [],
            "Documentation": [],
            "Other": [],
        }

        output = render_changelog_markdown(categories, version_label="v1.0.0")

        self.assertIn("## [v1.0.0]", output)
        self.assertIn("### Added", output)
        self.assertIn("- feat: new dashboard view (`1234567`)", output)
        self.assertIn("### Fixed", output)
        self.assertIn("- fix: button overflow on mobile (`89abcdef`)", output)
        self.assertNotIn("### Changed", output)  # empty categories should be omitted


if __name__ == "__main__":
    unittest.main()
