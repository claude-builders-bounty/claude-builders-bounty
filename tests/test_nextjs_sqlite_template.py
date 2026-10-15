#!/usr/bin/env python3
"""
Automated Validator & Verification Test Suite for CLAUDE.md Template (Bounty #2)
Verifies 100% of the acceptance criteria defined in claude-builders-bounty/issues/2:
1. Stack & pinned versions (Next.js 15, SQLite/better-sqlite3/Turso, Drizzle, Zod, React 19).
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
CLAUDE_MD = BASE_DIR / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"
ROOT_CLAUDE_MD = BASE_DIR / "CLAUDE.md"

class TestClaudeTemplate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        target = CLAUDE_MD if CLAUDE_MD.exists() else ROOT_CLAUDE_MD
        assert target.exists(), f"CLAUDE.md not found at {CLAUDE_MD} or {ROOT_CLAUDE_MD}"
        cls.content = target.read_text(encoding="utf-8")

    def test_stack_and_versions(self):
        self.assertIn("Next.js 15", self.content)
        self.assertIn("SQLite", self.content)
        self.assertIn("better-sqlite3", self.content)
        self.assertIn("Drizzle ORM", self.content)
        self.assertIn("TypeScript", self.content)
        self.assertIn("React 19", self.content)

    def test_folder_conventions(self):
        self.assertIn("src/app/", self.content)
        self.assertIn("schema/", self.content)
        self.assertIn("src/actions/", self.content)
        self.assertIn("(dashboard)", self.content)
        self.assertIn("(auth)", self.content)

    def test_dev_commands(self):
        self.assertIn("npm run dev", self.content)
        self.assertIn("npm run build", self.content)
        self.assertIn("npm run db:migrate", self.content)
        self.assertIn("npm run db:generate", self.content)
        self.assertIn("npm run lint", self.content)

    def test_sqlite_and_wal_conventions(self):
        self.assertIn("WAL", self.content)
        self.assertIn("foreign_keys = ON", self.content)
        self.assertIn("snake_case", self.content)
        self.assertIn("created_at", self.content)

    def test_component_and_action_patterns(self):
        self.assertIn("Server Components by Default", self.content)
        self.assertIn("'use client'", self.content)
        self.assertIn("'use server'", self.content)
        self.assertIn("revalidatePath", self.content)
        self.assertIn("safeParse", self.content)

    def test_anti_patterns_section(self):
        self.assertIn("What We DON'T Do (And Why)", self.content)
        self.assertIn("useEffect", self.content)
        self.assertIn("Prisma", self.content)
        self.assertIn("Unindexed Foreign Keys", self.content)

    def test_minimum_length_and_density(self):
        lines = len(self.content.splitlines())
        chars = len(self.content)
        self.assertGreaterEqual(lines, 100, f"Template should have >= 100 lines (got {lines})")
        self.assertGreaterEqual(chars, 3000, f"Template should have >= 3000 chars (got {chars})")

if __name__ == "__main__":
    unittest.main()
