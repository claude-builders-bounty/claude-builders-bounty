#!/usr/bin/env python3
"""Validate the Next.js + SQLite CLAUDE.md template covers bounty criteria."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"


REQUIRED_PHRASES = [
    "Next.js 15 App Router",
    "SQLite",
    "better-sqlite3",
    "Turso",
    "Project Structure",
    "Naming Conventions",
    "SQL And Migration Conventions",
    "Component Patterns",
    "Dev Commands",
    "Anti-Patterns To Avoid",
    "Every rule below is intentional",
    "Reason:",
    "foreign_keys = ON",
    "server actions",
    "route handlers",
    "Zod",
]


def test_template_covers_acceptance_criteria() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    assert not missing, f"Missing required coverage: {missing}"

    assert text.count("Reason:") >= 8
    assert "app/" in text and "db/migrations/" in text and "server/actions/" in text
    assert "Do not" in text
    assert "pnpm dev" in text and "pnpm db:migrate" in text


if __name__ == "__main__":
    test_template_covers_acceptance_criteria()
    print("ok")
