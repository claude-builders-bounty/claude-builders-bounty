#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Fleet sandboxes sometimes mount /tmp noexec or non-writable; fall back to
# template .cache/smoke-workdirs (gitignored via root .gitignore).
scaffold_args=(
  --typescript
  --tailwind
  --eslint
  --app
  --src-dir
  --import-alias "@/*"
  --use-pnpm
  --skip-install
  --disable-git
  --yes
)

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm not found; enabling via corepack..."
  corepack enable
  corepack prepare pnpm@9 --activate
fi

WORKDIR=""
for base in "${TMPDIR:-/tmp}" "$ROOT/.cache/smoke-workdirs"; do
  mkdir -p "$base" 2>/dev/null || continue
  candidate="$(mktemp -d "$base/smoke.XXXXXX" 2>/dev/null)" || continue
  if ! touch "$candidate/.write-test" 2>/dev/null; then
    rm -rf "$candidate"
    continue
  fi
  rm -f "$candidate/.write-test"

  echo "Scaffolding Next.js 15 App Router project in $candidate..."
  if timeout 180 npx --yes create-next-app@15 "$candidate/app" "${scaffold_args[@]}"; then
    WORKDIR="$candidate"
    break
  fi
  rm -rf "$candidate"
done

if [ -z "$WORKDIR" ]; then
  echo "Unable to scaffold Next.js 15 project in a writable workdir (tried TMPDIR and $ROOT/.cache/smoke-workdirs)" >&2
  exit 1
fi
trap 'rm -rf "$WORKDIR"' EXIT

cp "$ROOT/CLAUDE.md" "$WORKDIR/app/CLAUDE.md"

node "$ROOT/validate-template.mjs" "$WORKDIR/app/CLAUDE.md"

test -f "$WORKDIR/app/CLAUDE.md"
test -d "$WORKDIR/app/src/app"
test -f "$WORKDIR/app/src/app/layout.tsx"
grep -q "Next.js 15" "$WORKDIR/app/CLAUDE.md"
grep -q "better-sqlite3" "$WORKDIR/app/CLAUDE.md"
grep -q "src/app/" "$WORKDIR/app/CLAUDE.md"
grep -q "## Stack & Versions" "$WORKDIR/app/CLAUDE.md"
grep -q "## Folder Structure" "$WORKDIR/app/CLAUDE.md"
grep -q "## SQL & Migration Conventions" "$WORKDIR/app/CLAUDE.md"
grep -q "## Component Patterns" "$WORKDIR/app/CLAUDE.md"
grep -q "## What We Don't Do" "$WORKDIR/app/CLAUDE.md"
grep -q "## Environment Variables" "$WORKDIR/app/CLAUDE.md"
grep -q "## When to Ask Clarifying Questions" "$WORKDIR/app/CLAUDE.md"
grep -q "## Auth and Authorization" "$WORKDIR/app/CLAUDE.md"
grep -q "## Route Handlers and APIs" "$WORKDIR/app/CLAUDE.md"
grep -q "## Testing Rules" "$WORKDIR/app/CLAUDE.md"
grep -q "## Greenfield Smoke Test" "$WORKDIR/app/CLAUDE.md"
grep -q "middleware.ts" "$WORKDIR/app/CLAUDE.md"

greenfield_section="$(sed -n '/^## Greenfield Smoke Test$/,$p' "$WORKDIR/app/CLAUDE.md" | sed '1d' | sed '/^## /q')"
greenfield_step3="$(echo "$greenfield_section" | grep '^3\.' || true)"
echo "$greenfield_step3" | grep -q "create-invoice.ts"
echo "$greenfield_step3" | grep -q "void-invoice.ts"

greenfield_step4="$(echo "$greenfield_section" | grep '^4\.' || true)"
echo "$greenfield_step4" | grep -q "requireOrgMember"

greenfield_step5="$(echo "$greenfield_section" | grep '^5\.' || true)"
echo "$greenfield_step5" | grep -q "db:migrate"
echo "$greenfield_step5" | grep -q "typecheck"

echo "Greenfield smoke test passed: CLAUDE.md is usable in a fresh Next.js 15 project."
