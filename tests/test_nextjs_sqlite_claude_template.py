from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"


def test_nextjs_sqlite_template_covers_required_sections():
    text = TEMPLATE.read_text(encoding="utf-8")

    required = [
        "## Stack and versions",
        "## Project structure",
        "## Dev commands",
        "## SQL and migration conventions",
        "## Component patterns",
        "## What we do not do and why",
    ]
    for heading in required:
        assert heading in text


def test_nextjs_sqlite_template_is_opinionated_and_specific():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "Next.js 15 App Router" in text
    assert "better-sqlite3" in text
    assert "Turso/libSQL" in text
    assert "Drizzle ORM" in text
    assert "Zod" in text
    assert "Never edit an already-applied migration" in text
    assert "Do not put database calls in Client Components" in text
    assert text.count("Reason:") >= 6
