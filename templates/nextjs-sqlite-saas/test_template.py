#!/usr/bin/env python3
"""Smoke test for the Next.js + SQLite SaaS CLAUDE.md template.

Verifies that the file:
  1. Exists at templates/nextjs-sqlite-saas/CLAUDE.md
  2. Contains every section the bounty acceptance criteria requires
  3. Mentions every anti-pattern the criteria list ("what we don't do")
  4. Is not so short that it would fail the "opinionated" requirement

Exits 0 on success, 1 on any failure. No external deps; just stdlib."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CLAUDE_MD = Path(__file__).parent / "CLAUDE.md"

REQUIRED_SECTIONS = [
    "Stack & versions",
    "Folder structure",
    "SQL / migration conventions",
    "Component patterns",
    "What we don't do (and why)",
]

# Things the bounty specifically said the CLAUDE.md should help a fresh
# Next.js + SQLite project understand without follow-up questions.
MUST_MENTION = [
    "Next.js",          # stack
    "TypeScript",       # stack
    "Drizzle",          # ORM
    "SQLite",           # database
    "pnpm",             # package manager
    "App Router",       # routing model
    "zod",              # validation
    "Vitest",           # testing
    re.compile(r"\bid\b"),  # table id convention
    "createdAt",        # timestamp convention
    "migrations",       # migration rules
    "Server Component", # component pattern
    "dangerouslySetInnerHTML",  # anti-pattern
    "useEffect",        # anti-pattern
    "useMemo",          # anti-pattern
    "Pages Router",     # anti-pattern
]

MIN_BYTES = 4000  # Lower bound for "opinionated" — generic templates fit in <2KB.


def fail(message: str) -> None:
    print(f"❌ {message}")


def main() -> int:
    if not CLAUDE_MD.exists():
        fail(f"missing: {CLAUDE_MD}")
        return 1

    text = CLAUDE_MD.read_text(encoding="utf-8")

    if len(text.encode("utf-8")) < MIN_BYTES:
        fail(
            f"file is only {len(text)} chars; bounty requires 'opinionated' — "
            f"expected at least {MIN_BYTES}"
        )
        return 1

    failures: list[str] = []

    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^##\s+.*{re.escape(section)}", text, re.MULTILINE):
            failures.append(f"missing required section: '{section}'")

    for needle in MUST_MENTION:
        if isinstance(needle, str):
            if needle not in text:
                failures.append(f"must mention '{needle}' (acceptance criterion)")
        else:
            # Compiled regex
            if not needle.search(text):
                failures.append(f"must match pattern '{needle.pattern}' (acceptance criterion)")

    if failures:
        for f in failures:
            fail(f)
        return 1

    word_count = len(text.split())
    print(
        f"✅ {CLAUDE_MD.name}: {word_count} words, "
        f"{len(text.encode('utf-8'))} bytes, "
        f"{len(REQUIRED_SECTIONS)}/{len(REQUIRED_SECTIONS)} sections, "
        f"{len(MUST_MENTION)}/{len(MUST_MENTION)} must-mention terms"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
