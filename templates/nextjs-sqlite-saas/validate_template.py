#!/usr/bin/env python3
"""Static acceptance checks for the Next.js + SQLite CLAUDE.md template."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "CLAUDE.md"
README = ROOT / "README.md"
GREENFIELD_NOTES = ROOT / "GREENFIELD_TEST_NOTES.md"
GREENFIELD_SMOKE = ROOT / "smoke_greenfield.py"
MIN_REASON_CLAUSES = 45
MIN_SMOKE_PROMPTS = 5

REQUIRED_HEADINGS = [
    "## Stack And Versions",
    "## Default Implementation Choices",
    "## Project Structure",
    "## Dev Commands",
    "## CI And Release Gates",
    "## Environment Rules",
    "## SQLite And Migration Rules",
    "## Database Client Contracts",
    "## Naming Conventions",
    "## Data Access Patterns",
    "## App Router Patterns",
    "## Testing Expectations",
    "## Anti-Patterns",
]

REQUIRED_SIGNALS = [
    "Next.js 15",
    "App Router",
    "SQLite",
    "Turso",
    "better-sqlite3",
    "Drizzle",
    "Zod",
    "Auth.js",
    "Stripe",
    "Vitest",
    "Playwright",
    "server action",
    "foreign_keys",
    "deleted_at",
    "reason:",
]

REQUIRED_README_MAPPINGS = [
    "Project structure",
    "DB migration rules",
    "Dev commands",
    "Patterns to follow",
    "Anti-patterns to avoid",
    "Opinionated reasons",
    "Greenfield usability",
    "Static acceptance check",
    "Executable greenfield smoke check",
]

REQUIRED_GREENFIELD_SIGNALS = [
    "## Expected Claude Code Behavior",
    "## Additional Smoke Prompt Matrix",
    "## Local Validation Notes",
    "## Static Acceptance Check",
    "Do not write files yet",
]

DISALLOWED_PLACEHOLDERS = [
    "TODO",
    "FIXME",
    "REPLACE_ME",
]


def missing_items(text: str, required: list[str]) -> list[str]:
    return [item for item in required if item not in text]


def smoke_prompt_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("| `"))


def main() -> int:
    text = TEMPLATE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    greenfield_notes = GREENFIELD_NOTES.read_text(encoding="utf-8")

    missing_headings = missing_items(text, REQUIRED_HEADINGS)
    missing_signals = missing_items(text, REQUIRED_SIGNALS)
    missing_readme_mappings = missing_items(readme, REQUIRED_README_MAPPINGS)
    missing_greenfield_signals = missing_items(greenfield_notes, REQUIRED_GREENFIELD_SIGNALS)
    missing_smoke_file = not GREENFIELD_SMOKE.exists()
    combined_text = text + readme + greenfield_notes
    placeholder_hits = [token for token in DISALLOWED_PLACEHOLDERS if token in combined_text]
    if "lorem ipsum" in combined_text.lower():
        placeholder_hits.append("lorem ipsum")
    reason_count = text.count("reason:")
    prompt_count = smoke_prompt_count(greenfield_notes)

    if (
        missing_headings
        or missing_signals
        or missing_readme_mappings
        or missing_greenfield_signals
        or missing_smoke_file
        or placeholder_hits
        or reason_count < MIN_REASON_CLAUSES
        or prompt_count < MIN_SMOKE_PROMPTS
    ):
        print("Template acceptance check failed.", file=sys.stderr)
        for heading in missing_headings:
            print(f"missing heading: {heading}", file=sys.stderr)
        for signal in missing_signals:
            print(f"missing signal: {signal}", file=sys.stderr)
        for mapping in missing_readme_mappings:
            print(f"missing README mapping: {mapping}", file=sys.stderr)
        for signal in missing_greenfield_signals:
            print(f"missing greenfield note signal: {signal}", file=sys.stderr)
        if missing_smoke_file:
            print(f"missing greenfield smoke script: {GREENFIELD_SMOKE}", file=sys.stderr)
        for token in placeholder_hits:
            print(f"placeholder token still present: {token}", file=sys.stderr)
        if reason_count < MIN_REASON_CLAUSES:
            print(
                f"only {reason_count} reason clauses; expected at least {MIN_REASON_CLAUSES}",
                file=sys.stderr,
            )
        if prompt_count < MIN_SMOKE_PROMPTS:
            print(
                f"only {prompt_count} smoke prompts; expected at least {MIN_SMOKE_PROMPTS}",
                file=sys.stderr,
            )
        return 1

    print("Template acceptance check passed.")
    print(f"Checked {len(REQUIRED_HEADINGS)} required headings and {len(REQUIRED_SIGNALS)} stack/pattern signals.")
    print(f"Checked {reason_count} opinionated reason clauses and {prompt_count} greenfield smoke prompts.")
    print("Checked README acceptance mapping, executable smoke script, and placeholder hygiene.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
