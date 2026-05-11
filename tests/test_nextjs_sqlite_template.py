#!/usr/bin/env python3
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"
SMOKE = ROOT / "samples" / "nextjs-sqlite-claude-smoke.md"


class NextSqliteClaudeTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEMPLATE.read_text(encoding="utf-8")

    def test_expected_sections_are_present(self):
        required_sections = [
            "## Stack And Versions",
            "## Folder Structure",
            "## Naming Conventions",
            "## Dev Commands",
            "## SQL And Migration Conventions",
            "## Component Patterns",
            "## Patterns To Follow",
            "## Anti-Patterns To Avoid",
        ]
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, self.text)

    def test_database_guidance_is_specific_to_sqlite(self):
        required_terms = [
            "better-sqlite3",
            "Turso/libSQL",
            "PRAGMA foreign_keys = ON",
            "db/migrations",
            "YYYYMMDDHHMM_description.sql",
            "transactions",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_rules_include_reasons(self):
        reason_count = len(re.findall(r"^Reason:", self.text, flags=re.MULTILINE))
        self.assertGreaterEqual(reason_count, 8)

    def test_template_is_not_generic(self):
        stack_terms = [
            "Next.js 15",
            "App Router",
            "React Server Components",
            "SQLite",
            "server actions",
            "Zod",
        ]
        for term in stack_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_smoke_evidence_matches_template_expectations(self):
        smoke = SMOKE.read_text(encoding="utf-8")
        expected_terms = [
            "create-next-app@15.5.18",
            "Claude Code",
            "without asking clarifying questions",
            "db/migrations/202605111030_create_invites.sql",
            "server/actions/invite-team-member.action.ts",
            "lib/validation/invite.schema.ts",
        ]
        for term in expected_terms:
            with self.subTest(term=term):
                self.assertIn(term, smoke)


if __name__ == "__main__":
    unittest.main()
