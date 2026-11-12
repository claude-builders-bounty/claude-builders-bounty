#!/usr/bin/env python3
"""
Validation test suite for Next.js 15 + SQLite SaaS CLAUDE.md Template
"""
import unittest
import os
import re


class TestClaudeTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "nextjs-sqlite", "CLAUDE.md"
        )
        with open(cls.template_path, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_file_exists_and_substantial(self):
        self.assertTrue(os.path.exists(self.template_path))
        self.assertGreater(len(self.content), 2000, "CLAUDE.md should be thorough and substantial")

    def test_required_sections_present(self):
        required_headers = [
            "1. Stack & Versions",
            "2. Folder Structure",
            "3. SQL & Migration Conventions",
            "4. Component & Server Action Patterns",
            "5. What We DON'T Do (and Why)",
            "6. Development & Migration Commands",
            "7. Naming Conventions",
        ]
        for header in required_headers:
            self.assertIn(header, self.content, f"Missing required section: '{header}'")

    def test_stack_coverage(self):
        key_tech = [
            "Next.js App Router",
            "better-sqlite3",
            "Turso",
            "Drizzle ORM",
            "Zod",
            "Tailwind CSS",
            "Vitest",
        ]
        for tech in key_tech:
            self.assertIn(tech.lower(), self.content.lower(), f"Missing stack technology reference: '{tech}'")

    def test_sqlite_pragmas_documented(self):
        pragmas = [
            "journal_mode = WAL",
            "foreign_keys = ON",
            "busy_timeout = 5000",
        ]
        for pragma in pragmas:
            self.assertIn(pragma, self.content, f"Missing critical SQLite PRAGMA configuration: '{pragma}'")

    def test_anti_patterns_have_reasons(self):
        self.assertIn("DON'T", self.content)
        # Verify that 'Why' rationales accompany rules
        why_count = len(re.findall(r"\*Why\*:", self.content))
        self.assertGreaterEqual(why_count, 5, "Every rule must include a concrete 'Why' rationale")

    def test_no_unresolved_placeholders(self):
        placeholders = ["TODO", "TBD", "[INSERT", "<INSERT", "REPLACE_ME"]
        for p in placeholders:
            self.assertNotIn(p, self.content, f"Found unresolved placeholder '{p}' in production template")


if __name__ == "__main__":
    unittest.main()
