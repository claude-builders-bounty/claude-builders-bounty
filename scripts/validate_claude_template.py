#!/usr/bin/env python3
"""Validate the Next.js + SQLite CLAUDE.md bounty template."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"

REQUIRED_SECTIONS = [
    "## Stack And Versions",
    "## Dev Commands",
    "## Folder Structure",
    "## Naming Conventions",
    "## SQL And Migration Rules",
    "## Server And Component Patterns",
    "## What We Do Not Do",
]

REQUIRED_TERMS = [
    "Next.js 15",
    "App Router",
    "SQLite",
    "better-sqlite3",
    "Turso",
    "Drizzle",
    "migration",
    "Server Components",
    "Client Components",
    "reason",
]


def validate_template(text: str) -> list[str]:
    errors: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Missing section: {section}")
    for term in REQUIRED_TERMS:
        if term.lower() not in text.lower():
            errors.append(f"Missing required term: {term}")
    if len(text.split()) < 650:
        errors.append("Template is too short to be opinionated and usable without modification")
    if "Do not" not in text:
        errors.append("Template must include anti-patterns to avoid")
    return errors


def main() -> int:
    text = TEMPLATE.read_text(encoding="utf-8")
    errors = validate_template(text)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"Validated {TEMPLATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
