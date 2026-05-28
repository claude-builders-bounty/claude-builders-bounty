from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "templates" / "nextjs-sqlite" / "CLAUDE.md"


class NextjsSqliteTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = CLAUDE_MD.read_text(encoding="utf-8")

    def test_required_sections_are_present(self) -> None:
        for heading in (
            "## Stack And Commands",
            "## Project Structure",
            "## Naming Conventions",
            "## Database Rules",
            "## Component Patterns",
            "## Anti-Patterns To Avoid",
        ):
            self.assertIn(heading, self.text)

    def test_core_stack_and_database_guidance_is_specific(self) -> None:
        for phrase in (
            "Next.js 15 App Router",
            "SQLite through Drizzle ORM",
            "better-sqlite3",
            "Turso/libSQL",
            "Migration files are append-only",
            "Every workspace-scoped query must include a workspace or membership check",
        ):
            self.assertIn(phrase, self.text)

    def test_commands_and_agent_response_rules_are_present(self) -> None:
        for command in ("npm run dev", "npm run typecheck", "npm run db:migrate"):
            self.assertIn(command, self.text)
        self.assertIn("After changes, report the exact commands run", self.text)


if __name__ == "__main__":
    unittest.main()
