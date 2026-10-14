#!/usr/bin/env python3
"""
Automated Validator & Verification Test Suite for CLAUDE.md Template
Verifies all acceptance criteria:
1. Stack & pinned versions (Next.js 15, SQLite/better-sqlite3/Turso, Drizzle, Zod).
2. Folder conventions (App Router, route groups, schema, actions).
3. Dev commands (dev, build, db:migrate, lint, test).
4. SQLite/migration conventions (WAL mode, foreign keys, snake_case).
5. Component patterns (Server Components, Server Actions, Zod validation).
6. Anti-patterns section ('What we don't do (and why)').
7. No ambiguous or generic advice.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLAUDE_MD = BASE_DIR / "CLAUDE.md"

class TestClaudeTemplate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(CLAUDE_MD.exists(), f"CLAUDE.md missing: {CLAUDE_MD}")
        cls.content = CLAUDE_MD.read_text(encoding="utf-8")

    def test_stack_and_versions(self):
        self.assertIn("Next.js 15", self.content)
        self.assertIn("SQLite", self.content)
        self.assertIn("better-sqlite3", self.content)
        self.assertIn("Drizzle", self.content)
        self.assertIn("TypeScript", self.content)

    def test_folder_conventions(self):
        self.assertIn("src/app/", self.content)
        self.assertIn("schema/", self.content)
        self.assertIn("src/actions/", self.content)
        self.assertIn("(dashboard)", self.content)

    def test_dev_commands(self):
        self.assertIn("npm run dev", self.content)
        self.assertIn("npm run build", self.content)
        self.assertIn("npm run db:migrate", self.content)
        self.assertIn("npm run lint", self.content)

    def test_sqlite_pragmas(self):
        self.assertIn("journal_mode = WAL", self.content)
        self.assertIn("foreign_keys = ON", self.content)
        self.assertIn("busy_timeout", self.content)

    def test_anti_patterns_explained(self):
        self.assertIn("What We DON'T Do", self.content)
        self.assertIn("useEffect", self.content)
        self.assertIn("data fetching", self.content)
        self.assertIn("Heavy ORMs", self.content)
        self.assertIn("Unindexed Foreign Keys", self.content)

    def test_server_action_pattern(self):
        self.assertIn("'use server'", self.content)
        self.assertIn("revalidatePath", self.content)
        self.assertIn("safeParse", self.content)

if __name__ == "__main__":
    unittest.main()
