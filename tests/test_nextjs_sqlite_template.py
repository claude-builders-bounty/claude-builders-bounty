#!/usr/bin/env python3
"""Validate that the Next.js + SQLite CLAUDE.md template covers the bounty criteria."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md"
README = ROOT / "templates" / "nextjs-sqlite-saas" / "README.md"
SMOKE = ROOT / "examples" / "nextjs-sqlite-claude-smoke.md"


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"missing expected text: {needle}"


def test_template_covers_expected_sections() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for heading in [
        "## Stack & Versions",
        "## Folder Structure",
        "## Naming Conventions",
        "## Dev Commands",
        "## SQL / Migration Conventions",
        "## Component Patterns",
        "## What We Do Not Do And Why",
    ]:
        assert_contains(text, heading)


def test_template_mentions_required_stack_and_rules() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for required in [
        "Next.js 15",
        "App Router",
        "better-sqlite3",
        "Turso/libSQL",
        "db/migrations",
        "Server Components",
        "Server Actions",
        "Zod",
        "Do not rewrite existing migrations.",
        "Every migration must be idempotent",
    ]:
        assert_contains(text, required)


def test_readme_setup_is_three_steps_or_fewer() -> None:
    text = README.read_text(encoding="utf-8")
    numbered_steps = [line for line in text.splitlines() if line.startswith(("1.", "2.", "3.", "4."))]
    assert 1 <= len(numbered_steps) <= 3


def test_smoke_output_exists() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    assert_contains(text, "fresh Next.js 15 App Router project")
    assert_contains(text, "without requiring extra clarifying questions")


if __name__ == "__main__":
    test_template_covers_expected_sections()
    test_template_mentions_required_stack_and_rules()
    test_readme_setup_is_three_steps_or_fewer()
    test_smoke_output_exists()
    print("nextjs_sqlite_template tests passed")
