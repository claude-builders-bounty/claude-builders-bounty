#!/usr/bin/env bash
set -euo pipefail

template="${1:-CLAUDE.md}"

required_patterns=(
  "Next.js 15"
  "SQLite"
  "Drizzle"
  "Folder Structure"
  "Naming Conventions"
  "SQL And Migration Rules"
  "Dev Commands"
  "Component Patterns"
  "What We Do Not Do"
  "better-sqlite3"
  "Turso"
  "Server Components"
  "server actions"
)

for pattern in "${required_patterns[@]}"; do
  if ! grep -Fq "$pattern" "$template"; then
    printf 'missing required pattern: %s\n' "$pattern" >&2
    exit 1
  fi
done

if grep -Eq 'generic|TODO|TBD|replace this' "$template"; then
  printf 'template still contains generic placeholder language\n' >&2
  exit 1
fi

printf 'CLAUDE.md template validation passed\n'
