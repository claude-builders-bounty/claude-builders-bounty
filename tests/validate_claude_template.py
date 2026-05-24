#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
text = (root / "CLAUDE-nextjs15-sqlite.md").read_text()

required_phrases = [
    "Next.js 15",
    "App Router",
    "SQLite",
    "Drizzle",
    "better-sqlite3",
    "Turso",
    "Folder structure",
    "Naming conventions",
    "migration",
    "Dev commands",
    "Patterns to follow",
    "Anti-patterns to avoid",
    "Every schema change requires",
    "Server Actions",
    "Client Components",
    "permissions",
    "PR checklist",
    "Reason:",
]

missing = [phrase for phrase in required_phrases if phrase not in text]
if missing:
    raise SystemExit(f"Missing required content: {missing}")

# Ensure it is genuinely opinionated, not a generic short checklist.
section_count = sum(1 for line in text.splitlines() if line.startswith("## "))
reason_count = text.count("Reason:")
if section_count < 10:
    raise SystemExit(f"Expected at least 10 sections, found {section_count}")
if reason_count < 8:
    raise SystemExit(f"Expected at least 8 explicit reasons, found {reason_count}")

print("CLAUDE.md template validation passed")
print(f"sections={section_count} reasons={reason_count} chars={len(text)}")
