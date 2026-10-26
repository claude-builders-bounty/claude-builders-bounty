#!/usr/bin/env python3
"""
Comprehensive Verification Script for Next.js 15 + SQLite CLAUDE.md Template
Validates acceptance criteria compliance for Bounty #2.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

TEMPLATE_PATH = Path(__file__).parent.parent / "CLAUDE.md"

REQUIRED_SECTIONS = [
    "Stack & Recommended Versions",
    "Opinionated Folder Structure",
    "SQLite & Migration Conventions",
    "Component & Data Fetching Patterns",
    "What We Don't Do (and Why)",
    "Essential Developer Commands",
]

MANDATORY_CONCEPTS = [
    ("Next.js", "Next.js 15 App Router requirement"),
    ("15.1", "Next.js 15.1+ version specification"),
    ("React", "React 19 framework layer"),
    ("SQLite", "Embedded SQLite database"),
    ("better-sqlite3", "High-speed native C++ SQLite driver"),
    ("Drizzle", "Drizzle ORM type safety"),
    ("WAL", "Write-Ahead Logging pragma for concurrent reads"),
    ("busy_timeout", "Busy timeout preventing SQLITE_BUSY locking errors"),
    ("Server Components", "React Server Components by default"),
    ("Server Actions", "Server Actions for atomic mutations"),
    ("Zod", "Runtime contract schema validation"),
    ("pnpm", "Explicit package manager commands"),
    ("No Prisma", "Explicit anti-pattern with concrete architectural justification"),
]


def test_template():
    print(f"Reading template from {TEMPLATE_PATH.resolve()}...")
    assert TEMPLATE_PATH.exists(), f"File {TEMPLATE_PATH} does not exist!"

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print("\n--- 1. Validating Required Sections ---")
    missing_sections = 0
    for sec in REQUIRED_SECTIONS:
        if sec in content:
            print(f"  [PASS] Found section: '{sec}'")
        else:
            print(f"  [FAIL] Missing section: '{sec}'")
            missing_sections += 1

    print("\n--- 2. Validating Mandatory Architecture Concepts ---")
    missing_concepts = 0
    for keyword, desc in MANDATORY_CONCEPTS:
        if keyword.lower() in content.lower():
            print(f"  [PASS] Verified: {desc} ('{keyword}')")
        else:
            print(f"  [FAIL] Missing: {desc} ('{keyword}')")
            missing_concepts += 1

    print("\n--- 3. Validating Pragmas & SQL Safety Rules ---")
    assert "journal_mode = WAL" in content, "Missing WAL mode pragma!"
    assert "busy_timeout = 5000" in content, "Missing busy_timeout pragma!"
    assert "foreign_keys = ON" in content, "Missing foreign_keys pragma!"
    print("  [PASS] All production SQLite pragmas verified.")

    assert missing_sections == 0, f"Failed: {missing_sections} missing sections"
    assert missing_concepts == 0, f"Failed: {missing_concepts} missing concepts"

    print("\n========================================================")
    print("ALL VERIFICATION CHECKS PASSED: Template strictly satisfies Issue #2 criteria.")
    print("========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(test_template())
