"""Unit test suite for the Next.js + SQLite CLAUDE.md template."""

from pathlib import Path
import pytest


def test_nextjs_sqlite_template_exists():
    template_path = Path(__file__).parent.parent / "templates" / "nextjs-sqlite" / "CLAUDE.md"
    assert template_path.exists(), "templates/nextjs-sqlite/CLAUDE.md does not exist"


def test_nextjs_sqlite_template_required_sections():
    template_path = Path(__file__).parent.parent / "templates" / "nextjs-sqlite" / "CLAUDE.md"
    content = template_path.read_text(encoding="utf-8")

    required_sections = [
        "Stack & Versions",
        "Folder Structure",
        "SQL & Migration Conventions",
        "Component & Code Patterns",
        "What We Don't Do",
    ]

    for section in required_sections:
        assert section.lower() in content.lower(), f"Missing required section: {section}"


def test_nextjs_sqlite_template_key_requirements():
    template_path = Path(__file__).parent.parent / "templates" / "nextjs-sqlite" / "CLAUDE.md"
    content = template_path.read_text(encoding="utf-8")

    key_requirements = [
        "Next.js 15",
        "SQLite",
        "better-sqlite3",
        "Drizzle",
        "WAL",
        "pnpm",
    ]

    for req in key_requirements:
        assert req.lower() in content.lower(), f"Missing key requirement topic: {req}"
