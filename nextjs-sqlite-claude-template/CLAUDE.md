# CLAUDE.md — Next.js 15 + SQLite SaaS

This project is a small SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React. Optimize for correctness, fast iteration, and simple deployment.

## Stack & versions

- Next.js 15 App Router
- React Server Components by default
- TypeScript strict mode
- SQLite via `better-sqlite3` for single-node apps or Turso/libSQL for hosted edge SQLite
- Drizzle ORM or Kysely for typed SQL
- Tailwind CSS for styling
- Vitest for unit tests and Playwright for critical flows

Reason: this stack keeps infrastructure small while preserving typed boundaries around data access.

## Folder structure

```text
app/
  (marketing)/          public pages
  (app)/                authenticated product pages
  api/                  route handlers only when HTTP is required
components/
  ui/                   low-level reusable UI
  forms/                form components with validation
  feature-name/         feature-specific components
lib/
  auth/                 session, auth helpers, permissions
  db/                   database client, schema, migrations
  env.ts                validated environment variables
  services/             server-side business logic
  validators/           zod schemas
server/
  actions/              server actions grouped by feature
  queries/              read-only database queries
  mutations/            write operations
migrations/             SQL migrations, append-only
scripts/                one-off operational scripts
tests/                  unit and integration tests
```

Rule: do not put database writes directly inside UI components. Use `server/mutations` or server actions so side effects are easy to audit.

## Naming conventions

- Components: `PascalCase.tsx`
- Hooks: `useThing.ts`
- Server actions: `thing.actions.ts`
- Queries: `thing.queries.ts`
- Mutations: `thing.mutations.ts`
- Zod schemas: `ThingInputSchema`
- Database tables: `snake_case` plural nouns
- TypeScript types: `PascalCase`

Reason: predictable names let Claude Code find the right layer without asking clarifying questions.

## Dev commands

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm lint
pnpm test
pnpm db:migrate
pnpm db:studio
```

If a command is missing, add it to `package.json` before inventing a one-off command.

## SQL / migration conventions

- Migrations are append-only. Never edit a migration that has been applied outside your local branch.
- Every schema change needs a migration and a short reason in the PR body.
- Use transactions for multi-step writes.
- Every table must have:
  - `id` primary key
  - `created_at`
  - `updated_at` where updates are possible
- Prefer soft deletes only when the product needs undo/audit; otherwise hard delete is acceptable for simple join rows.
- Add indexes for foreign keys and frequently filtered columns.
- Do not store secrets in SQLite. Store encrypted references or use environment-backed secret storage.

Reason: SQLite is reliable, but concurrency and migrations become painful when writes are scattered or schema history is rewritten.

## Data access rules

- `server/queries/*` is read-only.
- `server/mutations/*` is the only place for writes unless a feature has an explicit server action wrapper.
- Validate all external input with Zod before database writes.
- Return serializable DTOs from query functions; do not leak raw database rows into client components.
- Keep SQL close to the feature, but keep the DB client in `lib/db`.

## Component patterns

- Use Server Components by default.
- Add `"use client"` only for interactivity, browser APIs, or local component state.
- Keep client components small and pass them serializable props.
- Forms should use a schema from `lib/validators` and submit to a server action.
- Shared UI components should not import feature-specific services.

Reason: minimizing client components reduces bundle size and avoids accidental secret/database access in the browser.

## Server action pattern

```ts
"use server";

import { revalidatePath } from "next/cache";
import { CreateProjectSchema } from "@/lib/validators/project";
import { createProject } from "@/server/mutations/project.mutations";

export async function createProjectAction(input: unknown) {
  const parsed = CreateProjectSchema.parse(input);
  const project = await createProject(parsed);
  revalidatePath("/app/projects");
  return { ok: true, projectId: project.id };
}
```

Rules:
- Validate first.
- Call one mutation function.
- Revalidate only the paths affected.
- Return a small DTO.

## Auth and permissions

- Never trust client-provided user IDs.
- Derive `userId` from the server session.
- Permission checks live in `lib/auth/permissions.ts` or feature-specific policy files.
- Every mutation must check ownership or role before writing.

Reason: most SaaS data leaks come from missing ownership checks, not from complex exploits.

## Environment variables

- Define all env vars in `lib/env.ts`.
- Validate env vars at boot with Zod.
- Use separate names for public values: `NEXT_PUBLIC_*` only when safe for the browser.
- Never read `process.env` throughout the app; import from `lib/env.ts`.

## Error handling

- Throw typed/domain errors from services.
- Convert errors into user-safe messages at the route/action boundary.
- Do not expose SQL errors, stack traces, or secrets to clients.
- Log enough context to debug: feature, user ID, object ID, and operation.

## Testing rules

- Unit-test pure validators and service functions.
- Integration-test mutations using a temporary SQLite database.
- Playwright-test the signup/login/billing-critical flows.
- Every bug fix should add a regression test when practical.

## What we do not do and why

- Do not add global state libraries by default. Server state should come from queries/actions.
- Do not call the database from Client Components. It breaks security and bundling boundaries.
- Do not create API routes when a Server Action is enough. API routes are for webhooks, third-party clients, or public HTTP contracts.
- Do not edit old migrations. Create a new migration so deployed databases remain reproducible.
- Do not use `any` to silence type errors. Fix the type boundary or add a narrow explicit type.
- Do not add background jobs inside request handlers. Use a queue or scheduled script.
- Do not optimize for multi-region complexity before the product needs it. SQLite is chosen for simplicity.

## PR checklist for Claude Code

Before opening a PR:

- [ ] Run typecheck, lint, and relevant tests.
- [ ] Confirm database changes include migrations.
- [ ] Confirm every mutation has an auth/ownership check.
- [ ] Confirm new Client Components are necessary.
- [ ] Update README or feature docs when behavior changes.
- [ ] Include screenshots for UI changes.
