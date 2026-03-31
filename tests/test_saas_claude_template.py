import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"


class NextJsSqliteClaudeTemplateTests(unittest.TestCase):
    def test_template_exists(self):
        self.assertTrue(CLAUDE_MD.exists(), "CLAUDE.md template should exist")

    def test_template_covers_expected_sections(self):
        content = CLAUDE_MD.read_text(encoding="utf-8")
        for heading in [
            "# CLAUDE.md",
            "## Stack & Versions",
            "## Folder Structure",
            "## Dev Commands",
            "## SQL & Migration Rules",
            "## Component Patterns",
            "## What We Don't Do",
        ]:
            self.assertIn(heading, content)

    def test_template_is_opinionated_and_reasoned(self):
        content = CLAUDE_MD.read_text(encoding="utf-8")
        self.assertIn("Why:", content)
        self.assertIn("Do this", content)
        self.assertIn("Do not", content)
        self.assertIn("Next.js 15", content)
        self.assertTrue("SQLite" in content and ("better-sqlite3" in content or "Turso" in content))


if __name__ == "__main__":
    unittest.main()
