from __future__ import annotations

import pathlib
import re
import unittest


TEMPLATE = pathlib.Path(__file__).resolve().parents[1] / "CLAUDE.md"
TEXT = TEMPLATE.read_text(encoding="utf-8")
LOWER = TEXT.lower()


class NextSqliteTemplateTests(unittest.TestCase):
    def test_expected_sections_are_present(self) -> None:
        sections = [
            "Stack & Versions",
            "Folder Structure",
            "Naming Conventions",
            "Dev Commands",
            "SQL & Migration Conventions",
            "Database Access Rules",
            "Component Patterns",
            "What We Do Not Do",
        ]
        for section in sections:
            with self.subTest(section=section):
                self.assertIn(f"## {section}", TEXT)

    def test_stack_is_specific_to_next_15_and_sqlite(self) -> None:
        required_terms = [
            "Next.js 15",
            "App Router",
            "React Server Components",
            "better-sqlite3",
            "Turso",
            "SQLite",
            "Zod",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, TEXT)

    def test_migration_and_database_rules_are_concrete(self) -> None:
        required_patterns = [
            r"src/db/migrations",
            r"YYYYMMDDHHMM_description\.sql",
            r"IF NOT EXISTS",
            r"foreign keys",
            r"bound parameters",
            r"Only files under `src/db/repositories/\*` may import the database client",
        ]
        for pattern in required_patterns:
            with self.subTest(pattern=pattern):
                self.assertRegex(TEXT, pattern)

    def test_dev_commands_and_naming_conventions_are_included(self) -> None:
        for command in ["pnpm dev", "pnpm lint", "pnpm typecheck", "pnpm test", "pnpm db:migrate"]:
            with self.subTest(command=command):
                self.assertIn(command, TEXT)
        for convention in ["PascalCase", "camelCase", "SCREAMING_SNAKE_CASE", "snake_case"]:
            with self.subTest(convention=convention):
                self.assertIn(convention, TEXT)

    def test_anti_patterns_have_reasons(self) -> None:
        anti_pattern_section = TEXT.split("## What We Do Not Do", 1)[1].split("## Claude Code Operating Rules", 1)[0]
        bullets = [line for line in anti_pattern_section.splitlines() if line.startswith("- Do not")]
        self.assertGreaterEqual(len(bullets), 6)
        for bullet in bullets:
            with self.subTest(bullet=bullet):
                self.assertRegex(bullet, r"\b(because|so|when|without)\b")

    def test_template_is_not_generic(self) -> None:
        stack_specific_count = sum(
            LOWER.count(term)
            for term in [
                "sqlite",
                "server action",
                "server component",
                "repository",
                "migration",
                "account",
                "saas",
            ]
        )
        self.assertGreaterEqual(stack_specific_count, 40)
        self.assertNotIn("[todo", LOWER)
        self.assertNotIn("your framework", LOWER)


if __name__ == "__main__":
    unittest.main()
