from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validate_claude_template import TEMPLATE, validate_template


class ClaudeTemplateTests(unittest.TestCase):
    def test_template_contains_required_sections_and_terms(self) -> None:
        errors = validate_template(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(errors, [])

    def test_template_is_specific_to_next_sqlite_saas(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")
        expected_phrases = [
            "Next.js 15 App Router",
            "SQLite with Drizzle ORM migrations",
            "Server Actions for mutations",
            "Store money in integer minor units",
            "Do not add the Pages Router",
        ]
        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_template_path_matches_expected_drop_in_name(self) -> None:
        self.assertEqual(Path(TEMPLATE).name, "CLAUDE.md")


if __name__ == "__main__":
    unittest.main()
