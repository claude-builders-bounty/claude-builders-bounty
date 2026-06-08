#!/usr/bin/env python3
"""Validate the Next.js + SQLite CLAUDE.md template contains required guidance."""

from __future__ import annotations

from pathlib import Path


TEMPLATE = Path(__file__).with_name("CLAUDE.md")
REQUIRED_TERMS = [
    "Next.js",
    "SQLite",
    "Prisma",
    "Drizzle",
    "DATABASE_URL",
    "tenant",
    "billing",
    "typecheck",
    "migrations",
    "no secrets committed",
]


def main() -> int:
    content = TEMPLATE.read_text(encoding="utf-8")
    missing = [term for term in REQUIRED_TERMS if term.lower() not in content.lower()]
    if missing:
        raise SystemExit(f"Missing required guidance: {', '.join(missing)}")
    print(f"CLAUDE.md OK: {len(content.splitlines())} lines, {len(REQUIRED_TERMS)} required terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
