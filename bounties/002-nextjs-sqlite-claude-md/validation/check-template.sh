#!/usr/bin/env bash
set -euo pipefail

template="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/CLAUDE.md"

required_patterns=(
  "Next.js 15"
  "SQLite"
  "Drizzle"
  "## Stack & Versions"
  "## Folder Structure"
  "## Naming Conventions"
  "## SQL & Migration Conventions"
  "## Component Patterns"
  "## What We Do Not Do"
  "npm run db:generate"
  "npm run db:migrate"
  "better-sqlite3"
  "Turso"
  "Server Actions"
  "organization_id"
  "Never edit a migration"
)

for pattern in "${required_patterns[@]}"; do
  if ! grep -Fq "$pattern" "$template"; then
    echo "Missing required template coverage: $pattern" >&2
    exit 1
  fi
done

echo "nextjs sqlite claude template check passed"
