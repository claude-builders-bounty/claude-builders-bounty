#!/usr/bin/env python3
"""
Automated validation test for Next.js 15 + SQLite SaaS CLAUDE.md template.
Ensures all acceptance criteria specified in Bounty #2 are met.
"""

import os
import unittest

class TestSaaSClaudeTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.claude_path = os.path.join(base_dir, "CLAUDE.md")
        cls.readme_path = os.path.join(base_dir, "README.md")
        cls.schema_path = os.path.join(base_dir, "examples", "schema.ts")

        with open(cls.claude_path, "r", encoding="utf-8") as f:
            cls.claude_content = f.read()

    def test_required_files_exist(self):
        self.assertTrue(os.path.exists(self.claude_path), "CLAUDE.md must exist")
        self.assertTrue(os.path.exists(self.readme_path), "README.md must exist")
        self.assertTrue(os.path.exists(self.schema_path), "examples/schema.ts must exist")

    def test_expected_sections_present(self):
        sections = [
            "Stack & Versions",
            "Dev Commands",
            "Project & Folder Structure",
            "SQLite & Database Conventions",
            "Component & Server Action Patterns",
            "What We Don't Do (And Why)",
            "Naming Conventions"
        ]
        for sec in sections:
            self.assertIn(sec, self.claude_content, f"Missing section: {sec}")

    def test_stack_details(self):
        self.assertIn("Next.js 15", self.claude_content)
        self.assertIn("SQLite", self.claude_content)
        self.assertIn("better-sqlite3", self.claude_content)
        self.assertIn("Drizzle", self.claude_content)
        self.assertIn("TypeScript", self.claude_content)

    def test_sqlite_conventions(self):
        self.assertIn("WAL", self.claude_content)
        self.assertIn("foreign_keys", self.claude_content)
        self.assertIn("organization_id", self.claude_content)
        self.assertIn("pnpm db:migrate", self.claude_content)

    def test_antipatterns_explained(self):
        antipatterns = [
            "No API Routes for internal form mutations",
            "No `any` or loose casting",
            "No heavy ORMs",
            "No synchronous blocking DB calls on edge runtimes"
        ]
        for ap in antipatterns:
            self.assertIn(ap, self.claude_content, f"Missing anti-pattern explanation: {ap}")

if __name__ == "__main__":
    unittest.main()
