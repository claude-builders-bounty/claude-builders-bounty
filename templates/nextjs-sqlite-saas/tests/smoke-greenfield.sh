#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm not found; enabling via corepack..."
  corepack enable
  corepack prepare pnpm@9 --activate
fi

echo "Scaffolding Next.js 15 App Router project in $WORKDIR..."
timeout 180 npx --yes create-next-app@15 "$WORKDIR/app" \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-pnpm \
  --skip-install \
  --disable-git \
  --yes

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
grep -q "middleware.ts" "$WORKDIR/app/CLAUDE.md"

echo "Greenfield smoke test passed: CLAUDE.md is usable in a fresh Next.js 15 project."
