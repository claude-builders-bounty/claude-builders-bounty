#!/usr/bin/env python3
"""Verify that CLAUDE.md contains the required bounty sections."""

from __future__ import annotations

from pathlib import Path


REQUIRED_SECTIONS = [
    "## Stack and Versions",
    "## Folder Structure",
    "## Naming Conventions",
    "## Database and Migration Rules",
    "## Dev Commands",
    "## Repo Discovery Order",
    "## Component Patterns",
    "## Server Actions and Route Handlers",
    "## SQLite Conventions",
    "## What We Don't Do",
    "## Working Style",
    "## Defaults",
]


def main() -> int:
    path = Path(__file__).with_name("CLAUDE.md")
    content = path.read_text(encoding="utf-8")

    missing = [section for section in REQUIRED_SECTIONS if section not in content]
    if missing:
        print("Missing sections:")
        for section in missing:
            print(f"- {section}")
        return 1

    try:
        content.encode("ascii")
    except UnicodeEncodeError:
        print("CLAUDE.md contains non-ASCII characters.")
        return 1

    print("CLAUDE.md verification passed.")
    print(f"Checked {len(REQUIRED_SECTIONS)} required sections and ASCII cleanliness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
