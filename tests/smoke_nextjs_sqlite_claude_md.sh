#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_PATH="${ROOT_DIR}/templates/nextjs-sqlite-saas/CLAUDE.md"
TMP_ROOT="$(mktemp -d "${ROOT_DIR}/.tmp-nextjs-sqlite-claude.XXXXXX")"

cleanup() {
  case "${TMP_ROOT}" in
    "${ROOT_DIR}"/.tmp-nextjs-sqlite-claude.*) rm -rf "${TMP_ROOT}" ;;
  esac
}
trap cleanup EXIT

CLAUDE_BIN=""
if command -v claude >/dev/null 2>&1; then
  CLAUDE_BIN="$(command -v claude)"
elif command -v claude.exe >/dev/null 2>&1; then
  CLAUDE_BIN="$(command -v claude.exe)"
else
  echo "claude CLI is required for this smoke test" >&2
  exit 1
fi

PROJECT_DIR="${TMP_ROOT}/project"
mkdir -p \
  "${PROJECT_DIR}/src/app/(dashboard)/dashboard" \
  "${PROJECT_DIR}/src/components/ui" \
  "${PROJECT_DIR}/src/db/queries" \
  "${PROJECT_DIR}/src/lib" \
  "${PROJECT_DIR}/src/server/actions"

cp "${TEMPLATE_PATH}" "${PROJECT_DIR}/CLAUDE.md"

cat > "${PROJECT_DIR}/package.json" <<'JSON'
{
  "name": "nextjs-sqlite-saas-smoke",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "drizzle-orm": "^0.36.0",
    "better-sqlite3": "^11.0.0",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "vitest": "^2.1.0",
    "drizzle-kit": "^0.27.0"
  }
}
JSON

cat > "${PROJECT_DIR}/src/db/schema.ts" <<'TS'
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const organizations = sqliteTable("organizations", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
});
TS

OUTPUT_FILE="${TMP_ROOT}/claude-output.txt"

(
  cd "${PROJECT_DIR}"
  "${CLAUDE_BIN}" \
    --print \
    --model haiku \
    --tools "Read,Glob" \
    --max-budget-usd "${CLAUDE_SMOKE_MAX_BUDGET_USD:-0.30}" \
    "Using the project CLAUDE.md, give a concrete implementation plan for adding an organization billing settings page persisted in SQLite. Do not ask clarifying questions. Include file paths, database/migration steps, validation, and component/server boundaries."
) > "${OUTPUT_FILE}" 2>&1

if grep -Eiq "clarifying question|need to ask|before I can|can you clarify" "${OUTPUT_FILE}"; then
  echo "Claude asked for clarification instead of applying the template" >&2
  cat "${OUTPUT_FILE}" >&2
  exit 1
fi

if grep -Fq "as any" "${OUTPUT_FILE}"; then
  echo "Claude output used an unsafe 'as any' cast despite the template rules" >&2
  cat "${OUTPUT_FILE}" >&2
  exit 1
fi

for expected in \
  "src/app/(dashboard)" \
  "src/db/schema.ts" \
  "migration" \
  "zod" \
  "server action" \
  "organizationId"
do
  if ! grep -Fiq "${expected}" "${OUTPUT_FILE}"; then
    echo "Claude output did not include expected template concept: ${expected}" >&2
    cat "${OUTPUT_FILE}" >&2
    exit 1
  fi
done

echo "Claude Code CLAUDE.md smoke test passed"
echo "--- Sample Claude output ---"
cat "${OUTPUT_FILE}"
