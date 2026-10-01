"""
Unit tests validating the Next.js + SQLite CLAUDE.md template.
"""

from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "nextjs-sqlite" / "CLAUDE.md"


def test_template_exists():
    assert TEMPLATE_PATH.exists(), f"CLAUDE.md template missing at {TEMPLATE_PATH}"


def test_template_sections():
    content = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Verify essential headers exist
    assert "# CLAUDE.md — Next.js + SQLite Project Guide" in content
    assert "## 🚀 Quick Reference Commands" in content
    assert "## 📐 Architecture & Conventions" in content
    assert "## 🎨 Code Style & Structure" in content
    assert "## 🔐 Security & Error Handling" in content


def test_template_key_guidelines():
    content = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Verify Next.js App Router guidelines
    assert "Server Components by Default" in content
    assert "Server Actions" in content
    assert "use client" in content

    # Verify SQLite security and performance guidelines
    assert "PRAGMA journal_mode = WAL;" in content
    assert "Parameterized Queries" in content or "parameterized queries" in content
    assert "Transaction Safety" in content


def test_template_commands():
    content = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Verify essential npm scripts are listed
    assert "npm run dev" in content
    assert "npm run build" in content
    assert "npm run lint" in content
    assert "npm run typecheck" in content
    assert "npm run db:migrate" in content
