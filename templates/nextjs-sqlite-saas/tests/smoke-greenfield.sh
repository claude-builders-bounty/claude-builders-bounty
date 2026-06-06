#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "Scaffolding Next.js 15 App Router project in $WORKDIR..."
npx --yes create-next-app@15 "$WORKDIR/app" \
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

node "$ROOT/validate-template.mjs"

test -f "$WORKDIR/app/CLAUDE.md"
grep -q "Next.js 15" "$WORKDIR/app/CLAUDE.md"
grep -q "better-sqlite3" "$WORKDIR/app/CLAUDE.md"
grep -q "src/app/" "$WORKDIR/app/CLAUDE.md"

echo "Greenfield smoke test passed: CLAUDE.md is usable in a fresh Next.js 15 project."
