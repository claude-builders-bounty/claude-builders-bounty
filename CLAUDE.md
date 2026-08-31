# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the single source of truth when working on the **Next.js 15 App Router + SQLite** SaaS codebase. Every recommendation below is opinionated and tied to a concrete maintainability, performance, or correctness goal.

## Project Identity

- **Stack**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, SQLite via `better-sqlite3` (local/dev) or Turso (production).
- **Runtime**: Node.js 22 LTS. Prefer server components and Server Actions; use client components only for interactive UI.
- **Package manager**: `npm` with lockfile. Do not introduce `yarn` or `pnpm` without explicit approval.

## Directory Layout

```
app/              # App Router routes, layouts, loading/error UI
components/       # Shared presentational components (Server by default)
features/         # Domain-scoped modules: hooks, actions, schemas, queries
lib/              # Cross-cutting utilities: db client, auth, env validation
styles/           # Global CSS and Tailwind entry point
migrations/       # Sequential SQL migration files (001_, 002_, ...)
types/            # Shared TS types generated from DB schemas or handwritten
```

Rules:
- Keep route files in `app/` thin. Business logic belongs in `features/` or `lib/`.
- Co-locate tests next to the file they test: `foo.ts` ↔ `foo.test.ts`.
- Do not create `app/api` routes unless the feature genuinely needs a public HTTP API. Prefer Server Actions for internal mutations.

## Database & Migrations

- **Local**: `DATABASE_URL=file:./dev.sqlite` with `better-sqlite3`.
- **Production**: Turso (`LIBSQL_URL` + `LIBSQL_AUTH_TOKEN`).
- All schema changes must be expressed as numbered SQL migrations in `migrations/`.
- Migration naming: `migrations/001_create_users.sql`, `migrations/002_add_sessions.sql`.
- Apply migrations via `npm run db:migrate`. The script must be idempotent and fail loudly on conflict.
- Use explicit column types. Avoid nullable booleans; prefer `BOOLEAN NOT NULL DEFAULT 0`.
- Foreign keys are enabled by default (`PRAGMA foreign_keys = ON`). Write `ON DELETE` rules explicitly.
- Do not use raw SQL inside components. Use typed query helpers in `features/*/db.ts`.

## TypeScript Rules

- `strict: true` is non-negotiable.
- No `any`. Use `unknown` with narrow type guards when runtime shape is uncertain.
- Prefer explicit return types on Server Actions and API boundary functions.
- Environment variables are validated at startup via `lib/env.ts` using Zod. Never read `process.env` directly outside that module.

## Server Actions

- Place actions in `features/<domain>/actions.ts`.
- Every action must:
  1. Re-validate the user session.
  2. Validate input with Zod.
  3. Run the mutation.
  4. Call `revalidatePath` or `revalidateTag` as needed.
- Return typed results: `{ success: true, data: T } | { success: false, error: string }`.
- Never throw uncaught errors to the client; log and return safe error messages.

## Components

- Default to Server Components. Add `'use client'` only for interactivity (forms with `useActionState`, charts, animations).
- Keep components under 200 lines. Extract early when logic grows.
- Use Tailwind utility classes. No arbitrary values except for one-off marketing layouts.
- Form inputs must be associated with `<label>` and show validation errors from Server Actions.

## Styling

- Tailwind CSS v4 with CSS-first configuration in `app/globals.css`.
- Color tokens are semantic (`--color-surface`, `--color-panel`, `--color-ink`). Do not hard-code hex values in components.
- Dark mode is class-based. Test both themes before submitting UI changes.

## Auth & Security

- Use `iron-session` or compatible cookie-based sessions. No JWT in localStorage.
- Passwords hashed with `bcrypt` or `argon2`. Minimum cost factor 10.
- CSRF protection is handled by Next.js for Server Actions. Do not build custom CSRF middleware.
- Validate and sanitize every user input. Use parameterized queries only.

## Testing

- Unit tests: Vitest + React Testing Library for utilities and client components.
- Integration tests: test Server Actions against an in-memory SQLite database.
- E2E: Playwright for critical paths (sign up, login, checkout).
- Run `npm run check` (lint + type-check + test) before every push.

## Commands

```bash
npm run dev          # Start dev server
npm run build        # Production build (must pass type-check)
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Seed dev data
npm run check        # lint + type-check + test
```

## Anti-patterns

- Do not store secrets in `.env.local` and commit it. `.env.local` is gitignored; share dev values via 1Password.
- Do not fetch data in `useEffect` on the server. Use async Server Components.
- Do not create generic `utils.ts` files. Name utilities by what they do (`date.ts`, `currency.ts`).
- Do not add dependencies for tasks solvable by the standard library or existing packages.

## Pull Request Checklist

- [ ] `npm run check` passes locally.
- [ ] Migrations are included and reversible.
- [ ] New environment variables are documented in `lib/env.ts` and `.env.example`.
- [ ] UI changes work in both light and dark mode.
- [ ] Server Actions validate auth and input.

## Onboarding One-liner

Clone, `npm install`, copy `.env.example` to `.env.local`, run `npm run db:migrate && npm run dev`, then pick an issue from the tracker.
