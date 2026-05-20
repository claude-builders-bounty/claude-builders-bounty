from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_required_sections_are_present():
    required_sections = [
        "## Stack And Versions",
        "## Default Dev Commands",
        "## Folder Structure",
        "## Naming Conventions",
        "## SQLite And Migration Conventions",
        "## Component Patterns",
        "## Anti-Patterns To Avoid",
    ]

    for section in required_sections:
        assert section in TEMPLATE


def test_template_is_specific_to_nextjs_app_router_and_sqlite():
    required_terms = [
        "Next.js 15",
        "App Router",
        "SQLite",
        "better-sqlite3",
        "Turso",
        "workspace_id",
        "PRAGMA foreign_keys = ON",
        "server action",
    ]

    for term in required_terms:
        assert term in TEMPLATE


def test_rules_are_opinionated_with_reasons():
    assert TEMPLATE.count("Reason:") >= 20
    assert "Do not create a `pages/` directory." in TEMPLATE
    assert "Do not use `SELECT *`." in TEMPLATE
    assert "Do not store dates as local time strings." in TEMPLATE


def test_dev_commands_are_copy_ready():
    for command in [
        "pnpm dev",
        "pnpm lint",
        "pnpm typecheck",
        "pnpm test",
        "pnpm db:migrate",
        "pnpm build",
    ]:
        assert command in TEMPLATE
