#!/usr/bin/env bash
# Install reference-app deps and run Vitest unit + integration suites.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v pnpm >/dev/null 2>&1; then
  corepack enable
  corepack prepare pnpm@9 --activate
fi

pnpm install --frozen-lockfile 2>/dev/null || pnpm install
pnpm lint
pnpm test
