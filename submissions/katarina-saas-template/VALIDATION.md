# Validation — 2026-10-14

- Root CLAUDE.md: 131 lines, below the 500-line limit.
- Python SQLite unit tests: 6/6 passed (idempotence, checksum drift,
  failed migration rollback, upgrade preservation, tenant foreign key,
  parameterized injection attempt).
- TypeScript: `npm run typecheck` passed.
- Next.js 15.5.27: `npm run build` passed, including static generation
  and the dynamic `/api/projects` route.
- Dependencies were installed with lifecycle scripts disabled.

These tests exercise Python's real SQLite database engine and compile the
better-sqlite3 repository boundary. They do not prove that the native
better-sqlite3 binding works in every deployment environment, nor verify a
complete authentication or billing system. Auth is deliberately fail-closed.

The authenticated Claude Code acceptance run remains **pending**: no
authenticated Claude Code CLI is available in this environment. README.md
contains a reproducible prompt and the evidence to collect. This submission
must remain a draft until that acceptance requirement is verified.
