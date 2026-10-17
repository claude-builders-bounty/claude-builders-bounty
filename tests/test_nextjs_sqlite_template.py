"""
Unit tests for Issue #2: Next.js 15 App Router + SQLite CLAUDE.md template.
Validates all acceptance criteria, mandatory sections, and architectural guardrails.
"""

from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "nextjs-sqlite"
CLAUDE_MD = TEMPLATE_DIR / "CLAUDE.md"
README_MD = TEMPLATE_DIR / "README.md"


def test_template_files_exist():
    assert CLAUDE_MD.exists(), "CLAUDE.md template must exist"
    assert README_MD.exists(), "README.md template must exist"
    assert CLAUDE_MD.stat().st_size > 1000, "CLAUDE.md must contain comprehensive instructions"


def test_expected_sections_present():
    content = CLAUDE_MD.read_text(encoding="utf-8")
    
    # Required sections from Issue #2 specification
    assert "Stack & Tech Specifications" in content or "Stack & versions" in content
    assert "Directory & File Organization" in content or "Folder structure" in content
    assert "Database & SQL Conventions" in content or "SQL / migration conventions" in content
    assert "Component Patterns" in content or "Component patterns" in content
    assert "What We DON'T Do" in content or "What we don't do" in content


def test_sqlite_and_nextjs15_guardrails():
    content = CLAUDE_MD.read_text(encoding="utf-8")
    
    # SQLite critical configurations
    assert "journal_mode = WAL" in content, "Must configure SQLite WAL mode"
    assert "foreign_keys = ON" in content, "Must enforce foreign keys"
    assert "better-sqlite3" in content or "Turso" in content
    assert "drizzle" in content, "Must specify type-safe ORM (Drizzle)"
    
    # Next.js 15 App Router patterns
    assert "use server" in content, "Must document Server Actions pattern"
    assert "revalidatePath" in content, "Must document Next.js cache revalidation"
    assert "safeParse" in content or "zod" in content.lower(), "Must enforce Zod validation"


def test_anti_patterns_explained():
    content = CLAUDE_MD.read_text(encoding="utf-8")
    
    # Strict anti-patterns with rationale
    assert "useEffect" in content, "Must forbid useEffect for initial data fetching"
    assert "SQL injection" in content or "injection" in content.lower(), "Must explain SQL safety"
    assert "barrel" in content.lower() or "re-export" in content.lower(), "Must warn against barrel re-exports"


def test_readme_setup_steps():
    content = README_MD.read_text(encoding="utf-8")
    assert "Quick Start" in content
    assert "3 Steps" in content or "3 steps" in content.lower()
