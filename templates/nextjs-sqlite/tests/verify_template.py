#!/usr/bin/env python3
"""
Verification Script for Next.js 15 + SQLite CLAUDE.md Template
Validates acceptance criteria compliance for Bounty #2.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

TEMPLATE_PATH = Path(__file__).parent.parent / "CLAUDE.md"

REQUIRED_SECTIONS = [
    "Stack & Versions",
    "Essential Dev Commands",
    "Folder & File Structure",
    "SQL & Migration Conventions",
    "Component & Data Fetching Patterns",
    "What We Don't Do (and Why)",
]

MANDATORY_CONCEPTS = [
    ("Next.js 15", "Next.js 15 requirement"),
    ("SQLite", "SQLite requirement"),
    ("Drizzle", "Drizzle ORM recommendation"),
    ("better-sqlite3", "better-sqlite3 driver"),
    ("WAL", "Write-Ahead Logging pragma"),
    ("Server Components", "RSC default pattern"),
    ("Server Actions", "Server Actions pattern"),
    ("pnpm", "Explicit package manager"),
    ("Zod", "Schema validation"),
    ("No Prisma", "Explicit anti-pattern with justification"),
]


def test_template():
    print(f"Reading template from {TEMPLATE_PATH}...")
    assert TEMPLATE_PATH.exists(), f"File {TEMPLATE_PATH} does not exist"

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print("\nValidating Required Sections...")
    missing_sections = 0
    for sec in REQUIRED_SECTIONS:
        if sec in content:
            print(f"✅ Found section: '{sec}'")
        else:
            print(f"❌ Missing section: '{sec}'")
            missing_sections += 1

    print("\nValidating Mandatory Architecture Concepts...")
    missing_concepts = 0
    for keyword, desc in MANDATORY_CONCEPTS:
        if keyword.lower() in content.lower():
            print(f"✅ Verified: {desc} ({keyword})")
        else:
            print(f"❌ Missing: {desc} ({keyword})")
            missing_concepts += 1

    assert missing_sections == 0, f"Missing {missing_sections} required sections"
    assert missing_concepts == 0, f"Missing {missing_concepts} mandatory architecture concepts"

    print("\n🎉 ALL CHECKS PASSED: Template strictly satisfies all Issue #2 acceptance criteria.")
    return 0


if __name__ == "__main__":
    sys.exit(test_template())
