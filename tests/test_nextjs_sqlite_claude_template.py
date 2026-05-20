import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"


class NextjsSqliteClaudeTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEMPLATE.read_text(encoding="utf-8")

    def test_required_acceptance_sections_are_present(self):
        required_headings = [
            "## Stack And Versions",
            "## Dev Commands",
            "## Folder Structure",
            "## Naming Conventions",
            "## SQL And Migration Rules",
            "## Component Patterns",
            "## Patterns To Follow",
            "## Anti-Patterns To Avoid",
            "## Pull Request Checklist",
        ]

        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.text)

    def test_template_is_specific_to_nextjs_15_and_sqlite_saas(self):
        required_terms = [
            "Next.js 15",
            "App Router",
            "SQLite",
            "better-sqlite3",
            "Turso",
            "workspace",
            "billing",
            "subscription",
            "foreign_keys = ON",
            "journal_mode = WAL",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_rules_are_opinionated_with_reasons(self):
        reason_count = self.text.count("Reason:")
        self.assertGreaterEqual(reason_count, 25)

    def test_anti_patterns_cover_common_saas_risks(self):
        anti_patterns = self.text.split("## Anti-Patterns To Avoid", 1)[1]
        for risk in ["business logic", "second ORM", "`any`", "Client Components"]:
            with self.subTest(risk=risk):
                self.assertIn(risk, anti_patterns)


if __name__ == "__main__":
    unittest.main()
