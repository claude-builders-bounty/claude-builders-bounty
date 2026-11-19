#!/usr/bin/env python3
"""
Test suite for Next.js 15 + SQLite SaaS CLAUDE.md template.
Verifies all acceptance criteria from Bounty Issue #2.
"""
import unittest
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent
CLAUDE_MD = TEMPLATE_DIR / "CLAUDE.md"
README_MD = TEMPLATE_DIR / "README.md"

class TestClaudeTemplate(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CLAUDE_MD.exists(), "CLAUDE.md must exist")
        self.content = CLAUDE_MD.read_text(encoding="utf-8")

    def test_required_sections_present(self):
        required_headers = [
            "## Stack & Core Versions",
            "## Architecture & Folder Structure",
            "## SQLite & Database Conventions",
            "## Development Patterns to Follow",
            "## Anti-Patterns & What We DO NOT Do",
        ]
        for header in required_headers:
            self.assertIn(header, self.content, f"Missing required section: {header}")

    def test_stack_coverage(self):
        keywords = ["Next.js 15", "App Router", "SQLite", "better-sqlite3", "Turso", "Drizzle ORM", "TypeScript", "Zod", "Tailwind CSS"]
        for kw in keywords:
            self.assertIn(kw, self.content, f"Missing stack keyword: {kw}")

    def test_sqlite_pragmas_enforced(self):
        pragmas = [
            "journal_mode = WAL",
            "foreign_keys = ON",
            "busy_timeout = 5000",
            "synchronous = NORMAL",
        ]
        for pragma in pragmas:
            self.assertIn(pragma, self.content, f"Missing essential SQLite PRAGMA rule: {pragma}")

    def test_anti_patterns_explained(self):
        anti_patterns = [
            "NO `useEffect` for Data Fetching",
            "NO Client-Side DB Calls",
            "NO Raw Unparameterized SQL",
            "NO In-Memory State for Ephemeral DB Connections",
        ]
        for ap in anti_patterns:
            self.assertIn(ap, self.content, f"Missing anti-pattern guidance: {ap}")

    def test_readme_present_and_actionable(self):
        self.assertTrue(README_MD.exists(), "README.md must exist")
        readme_content = README_MD.read_text(encoding="utf-8")
        self.assertIn("CLAUDE.md", readme_content)
        self.assertIn("Next.js 15", readme_content)

if __name__ == "__main__":
    unittest.main()
