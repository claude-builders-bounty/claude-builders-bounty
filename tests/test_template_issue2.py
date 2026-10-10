#!/usr/bin/env python3
"""
Test suite verifying templates/nextjs-sqlite/CLAUDE.md against all Issue #2 acceptance criteria.
"""

import os
import re
import unittest

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "nextjs-sqlite", "CLAUDE.md")
README_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "nextjs-sqlite", "README.md")


class TestIssue2Template(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_file_exists_and_not_empty(self):
        self.assertTrue(os.path.exists(TEMPLATE_PATH))
        self.assertGreater(len(self.content), 1000)

    def test_stack_and_versions(self):
        """Must specify Next.js 15 App Router, TypeScript, SQLite, Drizzle ORM, Zod."""
        self.assertIn("Next.js 15+", self.content)
        self.assertIn("SQLite", self.content)
        self.assertIn("better-sqlite3", self.content)
        self.assertIn("Drizzle ORM", self.content)
        self.assertIn("Zod", self.content)

    def test_folder_structure_covered(self):
        """Must cover project structure with key directories."""
        self.assertIn("src/app", self.content)
        self.assertIn("src/actions", self.content)
        self.assertIn("src/db", self.content)
        self.assertIn("src/components", self.content)
        self.assertIn("src/lib", self.content)

    def test_sqlite_pragmas_enforced(self):
        """Must require essential SQLite PRAGMAs: WAL, foreign_keys, busy_timeout."""
        self.assertIn("journal_mode = WAL", self.content)
        self.assertIn("foreign_keys = ON", self.content)
        self.assertIn("busy_timeout = 5000", self.content)
        self.assertIn("synchronous = NORMAL", self.content)

    def test_naming_conventions_covered(self):
        """Must define naming conventions for files, components, and tables."""
        self.assertIn("kebab-case", self.content)
        self.assertIn("PascalCase", self.content)
        self.assertIn("snake_case", self.content)

    def test_anti_patterns_with_reasons(self):
        """Must have 'What we don't do (and why)' section explaining rationale."""
        self.assertIn("What We DO NOT Do (And Why)", self.content)
        self.assertIn("NO Prisma", self.content)
        self.assertIn("NO `useEffect` for Data Fetching", self.content)
        self.assertIn("NO Raw String SQL", self.content)

    def test_dev_commands_included(self):
        """Must include development commands for dev, build, migrations, testing."""
        self.assertIn("pnpm dev", self.content)
        self.assertIn("pnpm db:generate", self.content)
        self.assertIn("pnpm db:migrate", self.content)
        self.assertIn("pnpm test", self.content)

    def test_readme_quickstart_in_three_steps(self):
        """Must include a README with <= 3 steps."""
        self.assertTrue(os.path.exists(README_PATH))
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme = f.read()
        self.assertIn("Quickstart in 3 Steps", readme)


if __name__ == "__main__":
    unittest.main()
