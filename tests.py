#!/usr/bin/env python3
"""Tests for CLAUDE.md — validates structure, completeness, and quality."""

import re
from pathlib import Path

CLAUDE_MD = Path(__file__).parent / "CLAUDE.md"
CONTENT = CLAUDE_MD.read_text(encoding="utf-8")


def test_file_exists():
    """CLAUDE.md must exist at repo root."""
    assert CLAUDE_MD.exists(), "CLAUDE.md not found"


def test_line_count():
    """Must be reasonable length (under 700 lines)."""
    lines = CONTENT.strip().split("\n")
    assert len(lines) <= 700, f"CLAUDE.md is {len(lines)} lines (max 700)"
    assert len(lines) >= 100, f"CLAUDE.md is only {len(lines)} lines (need >= 100)" 


def test_has_stack_section():
    """Must cover stack and versions."""
    assert "Stack" in CONTENT, "Missing Stack & Versions section"
    assert "Next.js" in CONTENT, "Must mention Next.js"
    assert "SQLite" in CONTENT, "Must mention SQLite"


def test_has_folder_structure():
    """Must include project structure."""
    assert "Project Structure" in CONTENT or "Folder Structure" in CONTENT,         "Missing project/folder structure section"


def test_has_migration_conventions():
    """Must cover SQL/migration conventions."""
    assert "migration" in CONTENT.lower() or "Migration" in CONTENT,         "Missing migration conventions"
    assert "WAL" in CONTENT or "journal_mode" in CONTENT,         "Must mention WAL mode for SQLite"


def test_has_component_patterns():
    """Must cover component patterns."""
    assert "Server Component" in CONTENT or "server component" in CONTENT.lower(),         "Must cover Server Components"
    assert "use client" in CONTENT or '"use client"' in CONTENT,         "Must mention client components"


def test_has_anti_patterns():
    """Must include anti-patterns."""
    assert "Anti-Pattern" in CONTENT or "anti-pattern" in CONTENT.lower() or         "What we don" in CONTENT, "Missing anti-patterns section"


def test_has_dev_commands():
    """Must include dev commands."""
    assert "pnpm dev" in CONTENT or "npm run dev" in CONTENT or "dev" in CONTENT,         "Missing dev commands"


def test_has_why_explanations():
    """Rules must include reasoning (not just what)."""
    why_indicators = ["because", "why", "reward", "hides", "cost", "benefit"]
    found = sum(1 for w in why_indicators if w.lower() in CONTENT.lower())
    assert found >= 3, f"Only {found} 'why' explanations found (need >= 3)"


def test_has_sqlite_pragmas():
    """Must include SQLite pragma configuration."""
    assert "foreign_keys" in CONTENT, "Must mention foreign_keys pragma"
    assert "busy_timeout" in CONTENT, "Must mention busy_timeout pragma"


def test_has_zod_validation():
    """Must cover Zod validation."""
    assert "Zod" in CONTENT or "zod" in CONTENT, "Must mention Zod"
    assert "z.infer" in CONTENT, "Must show z.infer pattern"


def test_no_markdown_lint_errors():
    """Basic markdown lint checks."""
    lines = CONTENT.split("\n")
    errors = []
    for i, line in enumerate(lines, 1):
        if line.rstrip() != line and line.strip():
            errors.append(f"Line {i}: trailing whitespace")
    assert len(errors) == 0, f"Lint errors: {errors}"


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}: {test.__doc__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
