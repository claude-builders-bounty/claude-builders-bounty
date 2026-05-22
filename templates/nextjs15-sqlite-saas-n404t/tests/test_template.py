from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = (ROOT / "CLAUDE.md").read_text()


class TemplateAcceptanceTests(unittest.TestCase):
    def test_covers_required_sections(self):
        required = [
            "Stack and fixed choices",
            "Folder structure",
            "Naming conventions",
            "Database schema conventions",
            "Migration rules",
            "Component patterns",
            "What we do not do",
        ]
        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, CLAUDE)

    def test_includes_dev_commands(self):
        for command in [
            "pnpm dev",
            "pnpm build",
            "pnpm lint",
            "pnpm typecheck",
            "pnpm test",
            "pnpm db:generate",
            "pnpm db:migrate",
        ]:
            with self.subTest(command=command):
                self.assertIn(command, CLAUDE)

    def test_sqlite_and_migration_rules_are_specific(self):
        expected = [
            "SQLite",
            "Drizzle",
            "better-sqlite3",
            "Turso",
            "PRAGMA foreign_keys = ON",
            "Never edit applied migration files",
            "expand-copy-contract",
            "Store money in integer cents",
        ]
        for phrase in expected:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, CLAUDE)

    def test_every_anti_pattern_has_reason(self):
        section = CLAUDE.split("## What we do not do", 1)[1].split("## PR checklist", 1)[0]
        bullets = [line for line in section.splitlines() if line.startswith("- Do not")]
        self.assertGreaterEqual(len(bullets), 8)
        self.assertGreaterEqual(section.count("Reason:"), len(bullets))

    def test_greenfield_usability_prompt_exists(self):
        self.assertIn("Create initial workspace CRUD", CLAUDE)
        self.assertIn("Do not ask clarifying questions", CLAUDE)


if __name__ == "__main__":
    unittest.main()
