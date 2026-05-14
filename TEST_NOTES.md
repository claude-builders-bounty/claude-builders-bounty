# Issue #2 test notes

Bounty: TEMPLATE: `CLAUDE.md` for a Next.js 15 + SQLite SaaS project.

## Acceptance checklist

- Covers project structure: see sections 2, 3, 7.
- Covers naming conventions: see section 3.
- Covers DB migration rules: see section 4.
- Includes dev commands: see section 8.
- Includes patterns to follow: see sections 4–7, 9–13.
- Includes anti-patterns to avoid with reasons: see section 11.
- Opinionated, not generic: every major rule includes a reason and the template chooses boring SQLite-first SaaS defaults.
- Usable on a greenfield Next.js + SQLite project: the file assumes no app-specific domain and provides the initial structure.

## Dry-run prompt used for validation

> You are Claude Code in a new Next.js 15 App Router + SQLite SaaS repository. Read CLAUDE.md and propose the first implementation plan for adding workspace settings with a database-backed form. Do not ask clarifying questions unless the schema is ambiguous.

Expected behavior from the context:

1. Create/extend `migrations/0001_*` or the next numbered migration.
2. Put database queries/mutations under `lib/workspaces/` or `lib/db/`.
3. Add validation under `lib/validators/`.
4. Keep `app/(app)/.../page.tsx` as a Server Component.
5. Put interactive form UI in a small Client Component under `components/feature/`.
6. Use a Server Action for writes.
7. Run or document `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm db:migrate`.

This verifies the template gives Claude Code enough project context to proceed without asking basic structure or convention questions.
