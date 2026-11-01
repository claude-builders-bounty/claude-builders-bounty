#!/usr/bin/env bash
# Test that CLAUDE.md contains all required sections for the Next.js + SQLite
# SaaS template bounty. Exits 0 on pass, 1 on failure.

set -euo pipefail

FILE="CLAUDE.md"

if [[ ! -f "$FILE" ]]; then
  echo "FAIL: $FILE not found"
  exit 1
fi

required=(
  "Stack & versions"
  "Folder structure"
  "Dev commands"
  "SQL / migration conventions"
  "Component patterns"
  "Naming conventions"
  "What we don't do"
  "Testing"
  "next dev --turbopack"
  "better-sqlite3"
  "pnpm build"
  "INTEGER PRIMARY KEY"
  "deleted_at"
  "WHERE"
)

missing=0
for section in "${required[@]}"; do
  if ! grep -qF "$section" "$FILE"; then
    echo "FAIL: missing required content: $section"
    missing=1
  fi
done

# Must be opinionated: at least 3 "don't" / anti-pattern lines.
dont_count=$(grep -ciE "don't|anti-pattern|banned|never" "$FILE" || true)
if [[ "$dont_count" -lt 3 ]]; then
  echo "FAIL: expected at least 3 anti-pattern rules, found $dont_count"
  missing=1
fi

# Must be substantial (not a stub).
lines=$(wc -l < "$FILE")
if [[ "$lines" -lt 60 ]]; then
  echo "FAIL: CLAUDE.md too short ($lines lines)"
  missing=1
fi

if [[ "$missing" -eq 0 ]]; then
  echo "PASS: CLAUDE.md satisfies all acceptance criteria ($lines lines, $dont_count anti-pattern rules)"
  exit 0
else
  exit 1
fi
