from pathlib import Path

TEMPLATE = Path("templates/nextjs-sqlite/CLAUDE.md")
text = TEMPLATE.read_text(encoding="utf-8")
lower = text.lower()

required_phrases = [
    "next.js 15",
    "app router",
    "sqlite",
    "better-sqlite3",
    "turso",
    "project structure",
    "naming conventions",
    "migration conventions",
    "component patterns",
    "anti-patterns",
    "npm run dev",
    "npm run typecheck",
    "npm run lint",
    "npm run test",
    "pragma foreign_keys = on",
    "server components by default",
    "never trust route params as authorization proof",
]

missing = [phrase for phrase in required_phrases if phrase not in lower]
if missing:
    raise SystemExit(f"Missing required template content: {missing}")

reason_count = lower.count("reason:")
if reason_count < 8:
    raise SystemExit(f"Expected at least 8 opinionated reasons, found {reason_count}")

if len(text.splitlines()) < 180:
    raise SystemExit("Template is too short to be production-ready")

print(f"Template validation passed: {TEMPLATE} ({len(text.splitlines())} lines, {reason_count} reasons)")
