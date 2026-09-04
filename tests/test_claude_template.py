#!/usr/bin/env python3
"""
Validation and Structure Test Suite for Next.js + SQLite CLAUDE.md Template.
"""

import sys
import os
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "templates" / "nextjs-sqlite" / "CLAUDE.md"


class TestClaudeMdTemplate(unittest.TestCase):
    """Verify that CLAUDE.md contains all mandatory sections and opinionated rules."""

    def setUp(self):
        self.assertTrue(TEMPLATE_PATH.exists(), f"CLAUDE.md template missing at {TEMPLATE_PATH}")
        self.content = TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_expected_sections_present(self):
        expected_sections = [
            "## 1. Stack & Versions",
            "## 2. Project Directory Structure",
            "## 3. Development Commands",
            "## 4. SQLite & Migration Conventions",
            "## 5. Component & Data Flow Patterns",
            "## 6. What We DON'T Do (and Why)",
            "## 7. Claude Code Operational Protocol"
        ]
        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, self.content)

    def test_stack_details(self):
        self.assertIn("Next.js 15", self.content)
        self.assertIn("SQLite", self.content)
        self.assertIn("better-sqlite3", self.content)
        self.assertIn("Drizzle ORM", self.content)
        self.assertIn("Tailwind CSS", self.content)

    def test_sqlite_pragmas_documented(self):
        self.assertIn("WAL", self.content)
        self.assertIn("foreign_keys = ON", self.content)
        self.assertIn("busy_timeout = 5000", self.content)
        self.assertIn("synchronous = NORMAL", self.content)

    def test_anti_patterns_and_reasons(self):
        # Must document why specific patterns are avoided
        self.assertIn("DO NOT use Prisma", self.content)
        self.assertIn("DO NOT use `useEffect` for data fetching", self.content)
        self.assertIn("DO NOT use `any` in TypeScript", self.content)
        self.assertIn("DO NOT perform raw string interpolation in SQL", self.content)

    def test_component_architecture_rules(self):
        self.assertIn("Server Components by Default", self.content)
        self.assertIn("Client Components at the Leaves", self.content)
        self.assertIn("Server Actions for Mutations", self.content)


if __name__ == "__main__":
    unittest.main()
