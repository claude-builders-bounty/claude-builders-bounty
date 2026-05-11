import re
import unittest
from pathlib import Path


TEMPLATE_DIR = Path(__file__).resolve().parent
CLAUDE_MD = TEMPLATE_DIR / "CLAUDE.md"


class ClaudeTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = CLAUDE_MD.read_text(encoding="utf-8")

    def test_required_sections_are_present(self):
        required_sections = [
            "## Stack And Versions",
            "## Project Structure",
            "## Naming Conventions",
            "## Database And Migrations",
            "## Component Patterns",
            "## Dev Commands",
            "## Anti-Patterns To Avoid",
        ]

        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, self.content)

    def test_stack_and_commands_are_specific_to_nextjs_sqlite_saas(self):
        required_terms = [
            "Next.js 15",
            "App Router",
            "SQLite",
            "better-sqlite3",
            "Turso",
            "Server Actions",
            "React Server Components",
            "npm run db:migrate",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_opinionated_rules_include_reasons(self):
        rule_lines = re.findall(r"^- .+$", self.content, flags=re.MULTILINE)
        reason_count = self.content.count("Reason:")

        self.assertGreaterEqual(len(rule_lines), 45)
        self.assertGreaterEqual(reason_count, 40)

    def test_migration_guidance_is_actionable(self):
        self.assertIn("db/migrations/", self.content)
        self.assertIn("0004_add_workspace_members.sql", self.content)
        self.assertIn("BEGIN;", self.content)
        self.assertIn("COMMIT;", self.content)
        self.assertIn("Migrations are append-only after merge", self.content)


if __name__ == "__main__":
    unittest.main()
