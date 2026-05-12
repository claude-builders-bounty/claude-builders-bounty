#!/usr/bin/env python3
"""Validate the Next.js 15 SQLite SaaS CLAUDE.md bounty template."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "nextjs15-sqlite-saas" / "CLAUDE.md"
README = ROOT / "templates" / "nextjs15-sqlite-saas" / "README.md"
VALIDATION = ROOT / "templates" / "nextjs15-sqlite-saas" / "VALIDATION.md"


REQUIRED_SECTIONS = [
    "## Stack And Versions",
    "## Dev Commands",
    "## Folder Structure",
    "## Naming Conventions",
    "## Database And Migration Rules",
    "## Server Component Rules",
    "## Client Component Rules",
    "## Server Actions Pattern",
    "## Auth And Authorization",
    "## Testing Strategy",
    "## What We Do Not Do",
    "## Review Checklist",
]

REQUIRED_TERMS = [
    "Next.js 15",
    "App Router",
    "SQLite",
    "Turso",
    "better-sqlite3",
    "Drizzle",
    "Server Components",
    "Server Actions",
    "Zod",
    "Better Auth",
    "migration",
    "org_id",
    "anti-pattern",
]

REQUIRED_COMMANDS = [
    "pnpm dev",
    "pnpm build",
    "pnpm typecheck",
    "pnpm check",
    "pnpm db:generate",
    "pnpm db:migrate",
    "pnpm test",
    "pnpm e2e",
]

FORBIDDEN_PLACEHOLDERS = [
    "TODO",
    "FIXME",
    "your-app",
    "your app",
    "lorem",
]


def fail(message: str) -> None:
    print(f"validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    require(TEMPLATE.exists(), f"missing {TEMPLATE.relative_to(ROOT)}")
    require(README.exists(), f"missing {README.relative_to(ROOT)}")
    require(VALIDATION.exists(), f"missing {VALIDATION.relative_to(ROOT)}")

    text = TEMPLATE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        require(section in text, f"missing section {section}")

    lower_text = text.lower()
    for term in REQUIRED_TERMS:
        require(term.lower() in lower_text, f"missing required term {term}")

    for command in REQUIRED_COMMANDS:
        require(command in text or command.replace("pnpm ", '"') in text, f"missing command {command}")

    for placeholder in FORBIDDEN_PLACEHOLDERS:
        require(placeholder.lower() not in lower_text, f"placeholder remains: {placeholder}")

    reason_count = text.count("Reason:")
    require(reason_count >= 45, f"expected at least 45 reasons, found {reason_count}")

    antipattern_section = text.split("## What We Do Not Do", 1)[1].split("## Review Checklist", 1)[0]
    antipattern_rows = [
        line for line in antipattern_section.splitlines()
        if re.match(r"^\| [^|-].+\| .+\| Reason:", line)
    ]
    require(len(antipattern_rows) >= 10, f"expected at least 10 anti-pattern rows, found {len(antipattern_rows)}")

    require("Use In 3 Steps" in readme, "README must include 3-step usage")
    require("Smoke-Test Scenario" in validation, "validation notes must include smoke-test scenario")
    require(len(text.splitlines()) >= 220, "template is too shallow for the bounty")

    print(
        "validated Next.js 15 SQLite SaaS CLAUDE.md: "
        f"{len(text.splitlines())} lines, {reason_count} reasons, "
        f"{len(antipattern_rows)} anti-patterns"
    )


if __name__ == "__main__":
    main()
