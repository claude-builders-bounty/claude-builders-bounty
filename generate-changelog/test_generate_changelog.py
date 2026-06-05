#!/usr/bin/env python3
"""generate-changelog 的核心分类和渲染测试。"""

from __future__ import annotations

import unittest

from generate_changelog import Commit, classify, render_changelog


class GenerateChangelogTest(unittest.TestCase):
    def test_classifies_conventional_commits(self) -> None:
        self.assertEqual(classify("feat: add export command"), "Added")
        self.assertEqual(classify("fix(parser): handle empty tag"), "Fixed")
        self.assertEqual(classify("refactor: simplify grouping"), "Changed")
        self.assertEqual(classify("remove: delete legacy script"), "Removed")

    def test_classifies_keyword_commits(self) -> None:
        self.assertEqual(classify("add CLI installer"), "Added")
        self.assertEqual(classify("resolve changelog crash"), "Fixed")
        self.assertEqual(classify("drop deprecated flag"), "Removed")
        self.assertEqual(classify("update README"), "Changed")

    def test_render_changelog_has_required_sections(self) -> None:
        content = render_changelog(
            [
                Commit("abc1234", "feat: add CLI command"),
                Commit("def5678", "fix: repair parser"),
                Commit("9999999", "remove: delete old file"),
            ],
            tag="v1.0.0",
        )
        self.assertIn("## Unreleased", content)
        self.assertIn("### Added", content)
        self.assertIn("### Fixed", content)
        self.assertIn("### Changed", content)
        self.assertIn("### Removed", content)
        self.assertIn("Add CLI command (abc1234)", content)


if __name__ == "__main__":
    unittest.main()
