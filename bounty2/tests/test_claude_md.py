#!/usr/bin/env python3
"""Structural acceptance checks for bounty2/CLAUDE.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

REQUIRED_PHRASES = [
    "Next.js 15",
    "App Router",
    "SQLite",
    "better-sqlite3",
    "db/migrations",
    "org_id",
    "Zod",
    "amount_cents",
    "What we don't do",
    "pnpm",
    "Server Components",
    "PRAGMA foreign_keys",
]

REQUIRED_SECTIONS = [
    "## Stack & versions",
    "## Folder structure",
    "## Dev commands",
    "## SQL / migration rules",
    "## Component & data patterns",
    "## What we don't do",
]


def test_not_tiny():
    assert len(MD) > 2500, "CLAUDE.md too short to be opinionated"


def test_sections():
    missing = [s for s in REQUIRED_SECTIONS if s not in MD]
    assert not missing, f"missing sections: {missing}"


def test_phrases():
    missing = [p for p in REQUIRED_PHRASES if p not in MD]
    assert not missing, f"missing phrases: {missing}"


def test_anti_prisma_default():
    assert "Prisma" in MD and "Do not" in MD


if __name__ == "__main__":
    test_not_tiny()
    test_sections()
    test_phrases()
    test_anti_prisma_default()
    print("ok: bounty2 CLAUDE.md checks 4/4")
