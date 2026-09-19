import os
import pytest

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "nextjs-sqlite-saas", "CLAUDE.md")

def test_template_file_exists():
    assert os.path.exists(TEMPLATE_PATH), f"Template not found at {TEMPLATE_PATH}"

def test_template_required_sections():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify Expected Sections from Issue #2
    assert "Stack & Versions" in content
    assert "Directory & Folder Structure" in content or "Folder structure" in content
    assert "SQL & SQLite Database Conventions" in content or "SQL / migration" in content
    assert "Architectural & Component Patterns" in content or "Component patterns" in content
    assert "What We DO NOT Do" in content or "What we don't do" in content
    assert "Dev & Operational Commands" in content

def test_template_opinionated_rules_and_rationale():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify SQLite WAL mode and busy timeout
    assert "PRAGMA journal_mode = WAL" in content
    assert "PRAGMA busy_timeout = 5000" in content
    assert "PRAGMA foreign_keys = ON" in content

    # Verify Server Action pattern
    assert "'use server'" in content
    assert "ActionResult" in content

    # Verify Anti-patterns with "Why We Avoid It" table
    assert "Prisma ORM" in content
    assert "Why We Avoid It" in content
    assert "Drizzle ORM" in content
