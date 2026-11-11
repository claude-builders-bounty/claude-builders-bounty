import os
import unittest

class TestClaudeTemplate(unittest.TestCase):
    def setUp(self):
        self.template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "nextjs-sqlite", "CLAUDE.md")
        with open(self.template_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_required_sections_present(self):
        required_headers = [
            "Stack & Pinned Ecosystem",
            "Directory Hierarchy",
            "Database & Migration Invariants",
            "Component & Server Action Patterns",
            "Development & Testing Commands",
            "What We NEVER Do (And Why)"
        ]
        for header in required_headers:
            self.assertIn(header, self.content)

    def test_sqlite_invariants_specified(self):
        self.assertIn("PRAGMA journal_mode = WAL;", self.content)
        self.assertIn("PRAGMA foreign_keys = ON;", self.content)
        self.assertIn("better-sqlite3", self.content)
        self.assertIn("Turso", self.content)

    def test_nextjs15_patterns_specified(self):
        self.assertIn("Next.js 15", self.content)
        self.assertIn("App Router", self.content)
        self.assertIn('"use server";', self.content)
        self.assertIn("Zod", self.content)

if __name__ == "__main__":
    unittest.main()
