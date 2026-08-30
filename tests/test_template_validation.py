#!/usr/bin/env python3
import unittest
from pathlib import Path

class TestClaudeTemplateValidation(unittest.TestCase):
    def setUp(self):
        self.template_path = Path(__file__).resolve().parent.parent / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"
        self.assertTrue(self.template_path.exists(), "CLAUDE.md must exist")
        self.content = self.template_path.read_text()

    def test_required_sections_present(self):
        required_headers = [
            "Core Stack & Architecture",
            "Directory & File Structure",
            "Database & Migration Conventions",
            "Server Actions & Mutation Patterns",
            "Development Commands",
            "What We Do NOT Do (And Why)",
        ]
        for header in required_headers:
            self.assertIn(header, self.content, f"Missing section: {header}")

    def test_opinionated_anti_patterns_table(self):
        self.assertIn("use client", self.content)
        self.assertIn("Raw SQL concatenation", self.content)
        self.assertIn("NEXT_PUBLIC_*", self.content)

if __name__ == "__main__":
    unittest.main()
