#!/usr/bin/env bash
# Validates templates/nextjs-sqlite-saas for bounty issue #2 acceptance.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/templates/nextjs-sqlite-saas"
CLAUDE="$DIR/CLAUDE.md"
README="$DIR/README.md"

for f in "$CLAUDE" "$README" "$DIR/validation.md"; do
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 1; }
done

required_sections=(
  "Stack and versions"
  "Folder structure"
  "Database and migrations"
  "What we do not do"
  "Security checklist"
)
for section in "${required_sections[@]}"; do
  grep -q "$section" "$CLAUDE" || {
    echo "CLAUDE.md missing section: $section" >&2
    exit 1
  }
done

if grep -qE '^\|\|' "$CLAUDE" "$DIR/validation.md" 2>/dev/null; then
  echo "malformed markdown table (|| prefix)" >&2
  exit 1
fi

grep -q 'App Router' "$CLAUDE" || { echo "expected App Router guidance" >&2; exit 1; }
grep -q 'drizzle' "$CLAUDE" || { echo "expected Drizzle guidance" >&2; exit 1; }
grep -q 'Server Action' "$CLAUDE" || { echo "expected Server Action guidance" >&2; exit 1; }

echo "nextjs-sqlite-saas template validation passed"
