# Greenfield Test Notes

## Test scenario
A new Next.js 15 App Router + SQLite SaaS project receives the prepared `CLAUDE.md` at the repository root.

## Prompt used for conceptual smoke test
> Read CLAUDE.md and propose the first migration, route structure, and server-action pattern for a tiny B2B todo SaaS. Do not write files yet.

## Expected Claude behavior
- Uses Next.js 15 App Router and SQLite without asking for stack clarification.
- Proposes numbered migrations under `migrations/`.
- Includes tenant scoping with `org_id` or equivalent.
- Keeps auth and authorization server-side.
- Uses Server Components by default and small Client Components only for interactivity.
- Recommends validation gates: typecheck/lint/test/build and disposable DB migration check.

## Acceptance mapping
- Project structure: covered in `CLAUDE.md` section “Project structure”.
- Naming conventions: covered in “Naming conventions”.
- DB migration rules: covered in “SQL and migration rules”.
- Dev commands: covered in “Dev commands”.
- Patterns to follow: covered in data access, components, auth, billing, testing.
- Anti-patterns to avoid: covered in “What we do not do, and why”.
- Opinionated, not generic: each major rule includes a short reason.
