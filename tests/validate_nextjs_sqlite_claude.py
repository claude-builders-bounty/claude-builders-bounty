#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "templates" / "nextjs-sqlite" / "CLAUDE.md"


def require(text: str, needle: str) -> None:
    assert needle in text, f"Missing required text: {needle}"


def main() -> int:
    text = CLAUDE.read_text(encoding="utf-8")

    for section in [
        "## Stack & Versions",
        "## Folder Structure",
        "## Naming Conventions",
        "## Dev Commands",
        "## SQL & Migration Conventions",
        "## Component Patterns",
        "## What We Do Not Do",
    ]:
        require(text, section)

    for term in ["Next.js 15", "App Router", "SQLite", "better-sqlite3", "Turso", "Drizzle", "Zod"]:
        require(text, term)

    for command in ["pnpm dev", "pnpm lint", "pnpm typecheck", "pnpm test", "pnpm db:migrate"]:
        require(text, command)

    assert text.count("Reason:") >= 20, "Every major rule should explain why it exists"
    assert "Never edit a migration" in text
    assert "Do not use `SELECT *`" in text
    assert "Do not add a global state library" in text

    print(f"Validated {CLAUDE}: {len(text.splitlines())} lines, {text.count('Reason:')} reasons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
