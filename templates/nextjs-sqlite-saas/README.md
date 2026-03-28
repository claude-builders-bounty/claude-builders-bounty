# CLAUDE.md Template: Next.js 15 + SQLite SaaS

An opinionated `CLAUDE.md` for greenfield SaaS projects using Next.js 15 App Router, SQLite (better-sqlite3 locally, Turso in production), Drizzle ORM, NextAuth v5, and shadcn/ui.

## What this is

A drop-in `CLAUDE.md` that tells Claude Code exactly how to build in your stack. Paste it at the root of a new project and Claude will follow every convention without needing to be asked twice.

This is not a generic "best practices" document. Every rule is specific to the chosen stack and has an explicit reason. Rules without reasons are just cargo cult — Claude needs to understand *why* in order to apply them correctly in edge cases.

## Why each decision was made

### Next.js 15 App Router (not Pages Router)

Pages Router is legacy. App Router gives you React Server Components, streaming, and nested layouts. It's where the Next.js team invests. All new projects should start here. The CLAUDE.md explicitly rules out Pages Router patterns (e.g., `getServerSideProps`, `useEffect` for data fetching) because they're the most common source of confusion when switching from older projects.

### SQLite: better-sqlite3 locally, Turso in production

SQLite is underrated for SaaS. A single-tenant or low-to-medium-traffic SaaS can run on SQLite for years. The development experience is zero-config: no Docker, no Postgres service, no connection strings. Turso (built on libSQL, a fork of SQLite) makes SQLite production-viable by adding replication, edge deployment, and an HTTP interface compatible with serverless environments.

The DB connection singleton pattern in the template handles the local vs. production switch via env var detection, so the same code path works in both environments.

### Drizzle ORM (not Prisma)

Drizzle is SQL-first and migration-first. You write schema in TypeScript, generate SQL migrations with `drizzle-kit generate`, and apply them explicitly. There's no "auto-migrate in development" footgun. Prisma's migration story for SQLite is weaker, and Prisma Client has a heavy runtime footprint incompatible with edge deployments.

The strict rule against editing migration files manually is the single most important database rule. Drizzle tracks migration state in a journal; corruption there causes production incidents.

### NextAuth v5 (Auth.js)

v5 is a complete rewrite. It's Edge-compatible, works with the App Router's new data patterns, and has a first-party Drizzle adapter. The rule to always expose `user.id` in the session callback and always call `requireAuth()` first in Server Actions eliminates the most common auth bugs: missing user ID on the session and unauthenticated mutations.

### Server Actions vs API Routes

This distinction confuses most teams. The template codifies it as a rule: Server Actions for user-initiated mutations in your own UI, API Routes for external callers and custom HTTP semantics. Mixing them leads to duplicated auth logic and inconsistent error handling.

The `redirect()` inside `try/catch` anti-pattern is included because it is extremely common and completely silent — the redirect throws a special Next.js error that gets swallowed by the catch block, and the user never moves to the success page.

### TypeScript strict mode

`strict: true` is table stakes. The template adds `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` because they catch real bugs that `strict` alone misses. `noUncheckedIndexedAccess` makes `array[0]` return `T | undefined`, which prevents "cannot read properties of undefined" errors at runtime. `exactOptionalPropertyTypes` prevents passing `{ key: undefined }` where `{}` is expected.

The `as` cast rule is enforced because most `as` casts in application code are wrong — they're used to paper over type errors rather than fix them.

### Testing: Vitest + real in-memory SQLite

Mocking Drizzle is almost always wrong. The mock won't catch query syntax errors, constraint violations, or migration regressions. An in-memory SQLite database (`:memory:`) is fast (sub-millisecond), has no setup overhead, and gives you full fidelity. The template's `setup.ts` shows exactly how to do this.

Co-locating test files with source files is a deliberate choice. Tests in a separate `__tests__/` directory become orphaned when source files are moved or deleted. Co-location makes the relationship explicit.

### Playwright with role-based selectors

Playwright's `getByRole()` is resilient to styling changes and documents accessibility intent. CSS selectors break on Tailwind refactors. The rule to seed test data programmatically prevents slow, fragile UI-based setup.

### Environment variable validation with Zod

Missing env vars are a top cause of "works locally, fails in production" bugs. Validating at startup with Zod turns a runtime crash-at-first-use into an immediate startup failure with a clear error message. The `NEXT_PUBLIC_` secret anti-pattern is included because it's an extremely common and serious security mistake — secrets in `NEXT_PUBLIC_` vars are inlined into the client JS bundle and exposed to anyone who loads the page.

## How to use this template

1. Create a new Next.js project:
   ```bash
   pnpm create next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir
   ```

2. Copy `CLAUDE.md` to the project root.

3. Start a Claude Code session:
   ```bash
   cd my-saas
   claude
   ```

4. Claude will read `CLAUDE.md` and follow all conventions from the first prompt.

## Testing that Claude follows it

After pasting the template, verify Claude compliance by asking:

- "Add a user settings page where users can update their display name" — should produce a Server Action in `actions.ts`, not an API route, with `requireAuth()` at the top.
- "Add a new `posts` table" — should modify `schema.ts` and run `pnpm db:generate`, never hand-edit migrations.
- "Create a sidebar component" — should be a `'use client'` component if interactive, but the layout that contains it should remain a Server Component.
- "Fetch the user's posts on the dashboard" — should use a Server Component with direct DB access, not `useEffect` + `fetch`.

All four patterns are covered by explicit rules in the CLAUDE.md.
