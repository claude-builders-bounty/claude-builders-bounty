#!/usr/bin/env python3
"""
Automated verification suite for Next.js 15 + SQLite CLAUDE.md template.
Validates all acceptance criteria required by Issue #2.
"""
from pathlib import Path
import re

TEMPLATE_DIR = Path(__file__).resolve().parent.parent
CLAUDE_MD = TEMPLATE_DIR / "CLAUDE.md"

def test_file_exists():
    assert CLAUDE_MD.exists(), "CLAUDE.md must exist in template directory"
    print("✓ File existence check passed")

def test_required_sections():
    content = CLAUDE_MD.read_text(encoding="utf-8")
    required = [
        "Stack & Recommended Versions",
        "Opinionated Folder Structure",
        "SQLite Database & Migration Conventions",
        "Component & Data Mutation Patterns",
        "What We DON'T Do",
        "Greenfield Project Checklist"
    ]
    for sec in required:
        assert sec in content, f"Missing required section: {sec}"
    print("✓ All 6 required structural sections verified")

def test_sqlite_pragmas():
    content = CLAUDE_MD.read_text(encoding="utf-8")
    pragmas = [
        "journal_mode = WAL",
        "foreign_keys = ON",
        "busy_timeout = 5000",
        "synchronous = NORMAL"
    ]
    for p in pragmas:
        assert p in content, f"Missing essential SQLite production pragma: {p}"
    print("✓ All 4 essential SQLite production pragmas verified")

def test_anti_patterns():
    content = CLAUDE_MD.read_text(encoding="utf-8")
    assert "Direct Client DB Access" in content
    assert "useEffect" in content
    assert "Unindexed Foreign Keys" in content
    print("✓ Explicit anti-patterns & reasoning verified")

if __name__ == "__main__":
    test_file_exists()
    test_required_sections()
    test_sqlite_pragmas()
    test_anti_patterns()
    print("\n================ 100% TEMPLATE VERIFICATION PASSED ================")
