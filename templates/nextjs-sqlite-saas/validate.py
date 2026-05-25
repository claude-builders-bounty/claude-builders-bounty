#!/usr/bin/env python3
"""Validate that the Next.js SQLite SaaS CLAUDE.md covers the bounty sections."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLAUDE = ROOT / "CLAUDE.md"
FIXTURE = ROOT / "fixtures" / "greenfield-app" / "CLAUDE.md"

REQUIRED_PHRASES = (
    "Next.js 15 App Router",
    "SQLite",
    "Project Structure",
    "Naming Conventions",
    "Dev Commands",
    "SQL And Migration Conventions",
    "Component Patterns",
    "What We Do Not Do",
    "Reason:",
    "server-side authorization",
    "tenant",
)


def main() -> int:
    source = CLAUDE.read_text(encoding="utf-8")
    fixture = FIXTURE.read_text(encoding="utf-8")

    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in source]
    if missing:
        raise SystemExit(f"Missing required coverage: {', '.join(missing)}")

    if source != fixture:
        raise SystemExit("Fixture CLAUDE.md does not match the template.")

    print("CLAUDE.md template validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
