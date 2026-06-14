# CLAUDE.md — Next.js + SQLite SaaS Template

## Project Overview

This is a SaaS web application built with Next.js App Router, Drizzle ORM,
and Turso (SQLite). The project follows a feature-based directory structure
with server components by default and client components where interactivity
is required.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 14+ (App Router) |
| Language | TypeScript (strict mode) |
| Database | Turso (libSQL/SQLite via Drizzle ORM) |
| Auth | NextAuth.js v5 / Lucia Auth |
| Styling | Tailwind CSS |
| Linting | Biome (format + lint) |
| Testing | Vitest + Playwright |
| Package Manager | pnpm |

## Architecture

```
src/
├── app/          # Next.js App Router pages & API routes
│   ├── (auth)/   # Auth-required layouts (group)
│   ├── api/      # Route handlers (backend endpoints)
│   └── page.tsx  # Public landing page
├── components/   # Shared React components
│   ├── ui/       # Generic UI primitives (Button, Card, Input…)
│   └── forms/    # Form-specific components
├── db/           # Drizzle schema, migrations, queries
│   ├── schema/   # Table definitions
│   ├── queries/  # Reusable query functions
│   └── index.ts  # DB client (Turso/libSQL)
├── lib/          # Utility functions, middleware, config
├── actions/      # Server Actions (form handlers, mutations)
└── types/        # Shared TypeScript types
```

## Development Setup

```bash
pnpm install
pnpm db:push    # Push schema to local Turso/libSQL
pnpm db:seed    # Seed demo data
pnpm dev        # Start dev server (localhost:3000)
```

## Commands

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server |
| `pnpm build` | Production build |
| `pnpm check` | Biome lint + format check |
| `pnpm check:fix` | Auto-fix linter/formatter issues |
| `pnpm test` | Run Vitest unit tests |
| `pnpm test:e2e` | Run Playwright E2E tests |
| `pnpm db:push` | Push Drizzle schema to database |
| `pnpm db:generate` | Generate Drizzle migrations |
| `pnpm db:migrate` | Apply migrations |
| `pnpm db:seed` | Seed database with demo data |
| `pnpm typecheck` | Run TypeScript type checking |

## Coding Conventions

### Server Components (default)

- Prefer server components. Only add `"use client"` when you need:
  - useState / useEffect / useReducer
  - onClick / onChange / onSubmit
  - Browser-only APIs
  - Custom hooks that call the above

### Data Fetching

- Use Server Actions (`"use server"`) for mutations
- Use React Server Components for reads with async `await`
- Keep query logic in `src/db/queries/` for reuse
- Never call `fetch()` inside a server action if you can use the ORM directly

### Database

- All schema changes go through Drizzle migrations
- Foreign keys and unique constraints should be explicit in schema
- Use `$default` and `$onUpdate` for timestamps (`now()`)
- Soft deletes preferred: add `deletedAt: timestamp()` column

## Testing Patterns

- **Unit tests** (Vitest): test pure functions, server actions, query helpers
- **Integration tests**: test API route handlers with a test database
- **E2E tests** (Playwright): test critical user flows (signup, billing, CRUD)
- Test files co-locate with source: `component.test.tsx` next to `component.tsx`
- Use `test.db.ts` helper for isolated database per test

## `// biome-ignore` Usage

Suppress Biome linter/formatter warnings ONLY as a last resort.

**Acceptable use:**
- Third-party library incompatibility (e.g., `// biome-ignore lint/suspicious/noExplicitAny: <lib> types are loose`)
- Generated files that you don't control
- CSS-in-JS edge cases where Biome's CSS parser has a false positive

**Not acceptable:**
- To silence warnings you plan to fix later (create a TODO comment instead)
- To bypass type safety for convenience
- In application code without a specific, narrow explanation

Format: always include the exact rule ID and a reason:
```typescript
// biome-ignore lint/suspicious/noExplicitAny: <reason>
```

## Interacting with Claude

### Confirmation Style

- **Safe operations** (editing files, running tests, reading schema):
  Just do it, no need to ask.
- **Destructive operations** (db:reset, delete file, `rm -rf`):
  Ask for confirmation first.
- **New dependencies**: Propose with a one-line rationale before adding.

### Verbosity

- Be concise in responses unless asked for detail.
- For code changes, show only the changed section + 2 lines of context.
- Flag potential issues (performance, security, type safety) when you see them.

### PR Workflow

1. Run `pnpm check` and `pnpm test` before every commit
2. Prefix commits with type: `feat:`, `fix:`, `refactor:`, `db:`, `docs:`
3. Reference issues in commit messages: `fix: adjust timeout (closes #42)`
4. Keep PRs focused — one feature or fix per PR
5. Self-review: run `pnpm build` before marking PR ready

### When You're Stuck

- Look at `src/db/schema/` first to understand the data model
- Search by keyword in `src/` before writing new utilities
- If a query pattern already exists in `src/db/queries/`, follow it
- Ask the developer for clarification if the requirements are ambiguous
