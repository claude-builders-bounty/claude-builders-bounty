#!/usr/bin/env python3
"""
Test validation for CLAUDE.md template.
Verifies all expected sections and acceptance criteria are satisfied.
"""
import os

def test_claudemd_structure():
    with open("CLAUDE.md", "r", encoding="utf-8") as f:
        content = f.read()

    required_keywords = [
        "Next.js 15",
        "better-sqlite3",
        "Drizzle ORM",
        "PRAGMA journal_mode = WAL",
        "PRAGMA foreign_keys = ON",
        "PRAGMA busy_timeout",
        "Folder Structure" if "Folder" in content else "Directory & File Organization",
        "Server Components",
        "Server Actions",
        "Anti-Patterns",
        "pnpm dev",
        "pnpm db:migrate"
    ]

    for kw in required_keywords:
        assert kw.lower() in content.lower(), f"Missing required keyword/pattern: {kw}"

    print("[✓] ALL CLAUDE.md ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_claudemd_structure()
