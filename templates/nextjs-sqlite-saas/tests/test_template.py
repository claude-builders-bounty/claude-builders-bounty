"""
Automated Verification Suite for Next.js 15 + SQLite CLAUDE.md Template (#2).
"""

from pathlib import Path

def test_claudemd_template_completeness():
    template_path = Path(__file__).parent.parent / "CLAUDE.md"
    assert template_path.exists(), f"CLAUDE.md template missing at {template_path}"

    content = template_path.read_text(encoding="utf-8")

    # 1. Core Stack
    assert "Next.js 15" in content
    assert "SQLite" in content
    assert "Drizzle ORM" in content
    assert "better-sqlite3" in content
    assert "Turso" in content

    # 2. Key Sections
    assert "Stack & Pinned Versions" in content
    assert "Directory & File Conventions" in content
    assert "Essential Developer Commands" in content
    assert "SQLite Performance & Migration Invariants" in content
    assert "Architectural Patterns to Follow" in content
    assert "What We DON'T Do (and Why)" in content

    # 3. SQLite Invariants & PRAGMAs
    assert "journal_mode = WAL" in content
    assert "foreign_keys = ON" in content
    assert "busy_timeout" in content
    assert "drizzle-kit generate" in content
    assert "drizzle-kit migrate" in content

    # 4. Anti-patterns with rationale
    assert "No Client-Side Direct DB Queries" in content
    assert "No `useEffect` for Primary Data Fetching" in content
    assert "No Prisma with Serverless SQLite" in content
    assert "No `any` Types in TypeScript" in content

    # 5. Length and substantive quality
    lines = content.splitlines()
    assert len(lines) >= 80, f"Template should be comprehensive (found {len(lines)} lines)"

def test_sample_schema_validity():
    schema_path = Path(__file__).parent.parent / "sample-schema.ts"
    assert schema_path.exists(), f"sample-schema.ts missing at {schema_path}"

    content = schema_path.read_text(encoding="utf-8")
    assert "sqliteTable" in content
    assert "users" in content
    assert "teams" in content
    assert "subscriptions" in content
    assert "audit_logs" in content
    assert "index(" in content
