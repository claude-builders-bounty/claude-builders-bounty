from __future__ import annotations

import unittest

from scripts.generate_changelog import Commit, categorize, clean_subject, render_changelog


class GenerateChangelogTests(unittest.TestCase):
    def test_categorizes_common_commit_styles(self) -> None:
        cases = {
            "feat: add dashboard": "Added",
            "Add export button": "Added",
            "fix(parser): handle blank input": "Fixed",
            "remove legacy route": "Removed",
            "docs: update readme": "Changed",
        }
        for subject, category in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(categorize(subject), category)

    def test_clean_subject_removes_conventional_prefix(self) -> None:
        self.assertEqual(clean_subject("feat(api): add webhook"), "Add webhook")
        self.assertEqual(clean_subject("fix: repair edge case"), "Repair edge case")

    def test_renders_grouped_changelog(self) -> None:
        changelog = render_changelog(
            [
                Commit("abc1234", "feat: add import flow"),
                Commit("def5678", "fix: avoid duplicate entries"),
                Commit("fed4321", "remove old flag"),
            ],
            "v1.0.0",
        )
        self.assertIn("## Unreleased", changelog)
        self.assertIn("_Generated since `v1.0.0`._", changelog)
        self.assertIn("### Added", changelog)
        self.assertIn("- Add import flow (abc1234)", changelog)
        self.assertIn("### Fixed", changelog)
        self.assertIn("- Avoid duplicate entries (def5678)", changelog)
        self.assertIn("### Removed", changelog)
        self.assertIn("- Remove old flag (fed4321)", changelog)


if __name__ == "__main__":
    unittest.main()
