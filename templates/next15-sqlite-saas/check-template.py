#!/usr/bin/env python3
"""Static acceptance checks for the Next.js 15 SQLite CLAUDE template."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "CLAUDE.md"

REQUIRED_PHRASES = [
    "Next.js 15 App Router",
    "SQLite",
    "better-sqlite3",
    "Turso",
    "Project Structure",
    "Naming Conventions",
    "SQL And Migration Rules",
    "Dev Commands",
    "Component Patterns",
    "What We Do Not Do",
    "Completion Gates",
    "because",
]

REQUIRED_COMMANDS = [
    "pnpm install",
    "pnpm dev",
    "pnpm lint",
    "pnpm typecheck",
    "pnpm test",
    "pnpm db:migrate",
]


def bullet_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("- ")]


def main() -> int:
    text = TEMPLATE.read_text(encoding="utf-8")
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    missing.extend(command for command in REQUIRED_COMMANDS if command not in text)

    bare_rules = [
        line
        for line in bullet_lines(text)
        if "because" not in line.lower()
        and not line.startswith("- Next.js")
        and not line.startswith("- SQLite")
        and not line.startswith("- Zod")
        and not line.startswith("- Tailwind")
    ]

    if missing or bare_rules:
        for item in missing:
            print(f"missing required phrase: {item}")
        for line in bare_rules:
            print(f"rule without reason: {line}")
        return 1

    print("Template acceptance checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
