"""
Unit test suite verifying that the Next.js 15 + SQLite SaaS CLAUDE.md template
satisfies all specifications and acceptance criteria of Bounty #2.
Zero external dependencies (uses standard library unittest).
"""

from pathlib import Path
import re
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "templates" / "nextjs-sqlite" / "CLAUDE.md"
README_PATH = REPO_ROOT / "templates" / "nextjs-sqlite" / "README.md"


class TestClaudeTemplate(unittest.TestCase):
    def test_template_files_exist(self):
        """Verify both CLAUDE.md and README.md exist in the expected directory."""
        self.assertTrue(TEMPLATE_PATH.exists(), f"Missing template at {TEMPLATE_PATH}")
        self.assertTrue(README_PATH.exists(), f"Missing README at {README_PATH}")

    def test_required_sections_present(self):
        """Verify all required sections specified in Issue #2 exist as markdown headings."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")

        required_section_patterns = [
            r"##\s+1\.\s+Stack\s+&\s+Versions",
            r"##\s+2\.\s+Dev\s+Commands",
            r"##\s+3\.\s+Folder\s+Structure",
            r"##\s+4\.\s+SQL\s+&\s+SQLite\s+Migration\s+Conventions",
            r"##\s+5\.\s+Component\s+&\s+Architecture\s+Patterns",
            r"##\s+6\.\s+What\s+We\s+Don't\s+Do\s+\(And\s+Why\)",
        ]

        for pattern in required_section_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            self.assertIsNotNone(match, f"Required section pattern '{pattern}' not found in CLAUDE.md")

    def test_sqlite_pragmas_configured(self):
        """Ensure WAL mode, foreign keys, and busy timeout pragmas are explicitly defined."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("journal_mode = WAL", content)
        self.assertIn("foreign_keys = ON", content)
        self.assertIn("busy_timeout", content)

    def test_server_action_and_validation(self):
        """Ensure Server Actions and Zod schema validations are covered with concrete code."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('"use server"', content)
        self.assertIn("z.object", content)
        self.assertIn("revalidatePath", content)

    def test_anti_patterns_table_covers_rationale(self):
        """Ensure anti-patterns explain 'Why We Avoid It' and 'What To Do Instead'."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("What We Don't Do (And Why)", content)
        self.assertIn("Why We Avoid It", content)
        self.assertIn("What To Do Instead", content)
        self.assertIn("INTEGER", content)  # Financial precision currency integer rule


if __name__ == "__main__":
    unittest.main()
