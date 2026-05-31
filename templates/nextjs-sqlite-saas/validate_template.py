#!/usr/bin/env python3
"""Validate the Next.js + SQLite SaaS CLAUDE.md template."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "CLAUDE.md"

REQUIRED_PHRASES = [
    "Next.js 15 App Router",
    "SQLite",
    "Drizzle ORM",
    "Project Structure",
    "Migrations",
    "Server Actions",
    "Components",
    "Auth And Authorization",
    "Billing",
    "Testing",
    "What We Do Not Do",
    "PR Checklist",
    "Do not store money as floats",
    "Never edit a migration that has already shipped",
]


def main() -> int:
    text = TEMPLATE.read_text(encoding="utf-8")
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    if missing:
        raise SystemExit(f"Missing required template content: {', '.join(missing)}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
