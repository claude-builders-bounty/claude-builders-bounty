#!/usr/bin/env bash
# Install reference-app deps and run Vitest unit + integration suites.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../../.." && pwd)"
cd "$ROOT"

export DATABASE_URL="${DATABASE_URL:-:memory:}"
export SESSION_SECRET="${SESSION_SECRET:-Test-Session-Secret-32-Chars-Minimum-X9}"
export NEXT_PUBLIC_APP_URL="${NEXT_PUBLIC_APP_URL:-http://localhost:3000}"

on_err() {
  local exit_code=$?
  echo "reference run-tests failed: step exited with status ${exit_code} (line ${BASH_LINENO[0]})" >&2
  exit "$exit_code"
}
trap on_err ERR

if ! command -v pnpm >/dev/null 2>&1; then
  corepack enable
  corepack prepare pnpm@9 --activate
fi

echo "==> validate reference env vars"
node "${REPO_ROOT}/scripts/validate-reference-env.mjs"

echo "==> install dependencies"
pnpm install --frozen-lockfile 2>/dev/null || pnpm install

# Project-local temp dir avoids Vitest ENOENT flakes when /tmp is cleared mid-run.
mkdir -p "$ROOT/node_modules/.tmp"
export TMPDIR="$ROOT/node_modules/.tmp"

echo "==> lint"
pnpm lint

# CI runs migration tests then the full suite sequentially; vitest.config.ts uses
# project-local cacheDir + forks pool to avoid ENOENT flakes on shared cache.
echo "==> migration tests"
pnpm exec vitest run tests/db/migrations.test.ts

echo "==> full test suite"
pnpm test
