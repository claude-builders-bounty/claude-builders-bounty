#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates/nextjs15-sqlite/CLAUDE.md"


class NextJsSqliteClaudeMdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = TEMPLATE.read_text(encoding="utf-8")

    def test_required_sections_are_present(self) -> None:
        for heading in (
            "## Stack and Versions",
            "## Folder Structure",
            "## Commands",
            "## SQL and Migration Conventions",
            "## Server Component Patterns",
            "## Naming",
            "## What We Do Not Do",
            "## Definition of Done",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_required_operational_rules_are_present(self) -> None:
        for phrase in (
            "Next.js 15",
            "better-sqlite3",
            "Zod",
            "0001_create_users.sql",
            "PRAGMA foreign_keys = ON",
            "Server Component",
            "npm run db:migrate",
            "Do not put SQL in pages",
            "Do not create a `pages/` directory",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.content)

    def test_template_has_no_unresolved_placeholders(self) -> None:
        self.assertNotIn("TODO", self.content)
        self.assertNotIn("TBD", self.content)
        self.assertNotIn("<your", self.content.lower())


if __name__ == "__main__":
    unittest.main()
