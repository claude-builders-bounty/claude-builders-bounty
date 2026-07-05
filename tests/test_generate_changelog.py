import datetime as dt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_changelog import Commit, classify_commit, group_commits, render_changelog


class GenerateChangelogTests(unittest.TestCase):
    def test_classifies_common_commit_subjects(self):
        cases = {
            "feat: add bounty scanner": "Added",
            "fix: handle empty commit body": "Fixed",
            "docs: update setup steps": "Changed",
            "remove deprecated template": "Removed",
        }

        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(classify_commit(Commit("abc1234", subject)), expected)

    def test_renders_grouped_changelog_sections(self):
        commits = [
            Commit("a" * 40, "feat: add scanner"),
            Commit("b" * 40, "fix: repair parser"),
            Commit("c" * 40, "docs: update README"),
            Commit("d" * 40, "remove old template"),
        ]

        markdown = render_changelog(
            group_commits(commits),
            version="v1.0.0",
            since="v0.9.0",
            today=dt.date(2026, 7, 5),
        )

        self.assertIn("## v1.0.0 - 2026-07-05", markdown)
        self.assertIn("### Added", markdown)
        self.assertIn("- Add scanner (aaaaaaa)", markdown)
        self.assertIn("### Fixed", markdown)
        self.assertIn("- Repair parser (bbbbbbb)", markdown)
        self.assertIn("### Changed", markdown)
        self.assertIn("- Update README (ccccccc)", markdown)
        self.assertIn("### Removed", markdown)
        self.assertIn("- Remove old template (ddddddd)", markdown)


if __name__ == "__main__":
    unittest.main()
