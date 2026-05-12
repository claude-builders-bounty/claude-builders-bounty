# Next.js 15 + SQLite SaaS Project Guide

## Stack And Versions

- Use Next.js 15 with the App Router, React Server Components by default, and Server Actions only for mutations that benefit from colocated form handling.
- Use TypeScript in strict mode. Avoid `any`; use `unknown` at boundaries and narrow explicitly.
- Use SQLite for local development and small deployments. Prefer `better-sqlite3` for embedded deployments and Turso/libSQL when remote access, replication, or edge-adjacent reads are needed.
- Use a thin validation layer with Zod at all request, form, webhook, and environment-variable boundaries.

## Folder Structure

- `app/`: Route segments, layouts, loading states, and server-only page composition.
- `app/(marketing)/`: Public pages with no authenticated data requirements.
- `app/(app)/`: Authenticated product pages and account-level navigation.
- `components/`: Reusable presentational components that do not access the database directly.
- `features/<feature>/`: Feature-owned UI, actions, queries, schemas, and tests.
- `lib/db/`: Database connection, migrations, query helpers, and transaction utilities.
- `lib/auth/`: Session resolution, role checks, and auth provider adapters.
- `lib/env.ts`: Single parsed environment contract. Nothing reads `process.env` directly outside this file.
- `tests/`: Unit and integration tests that are not colocated with feature code.

Reason: route files stay small, feature code remains discoverable, and database access is kept out of generic UI.

## Naming Conventions

- Use `getX` for read-only data loaders and `createX`, `updateX`, `deleteX` for mutations.
- Use `requireUser()` when missing auth is exceptional and `getUser()` when anonymous access is valid.
- Name Server Actions with an `Action` suffix, for example `updateWorkspaceAction`.
- Name database tables in snake_case and TypeScript types in PascalCase.
- Name files by role: `queries.ts`, `actions.ts`, `schema.ts`, `permissions.ts`, `page.tsx`.

Reason: predictable names reduce context hunting and make access patterns obvious.

## SQL And Migration Conventions

- Every schema change must be represented by a migration file committed with the feature.
- Migrations are append-only. Never edit a migration that has reached `main`.
- Wrap multi-step writes in a transaction and keep transaction scope small.
- Use explicit column lists in inserts and selects. Avoid `SELECT *`.
- Add indexes with the query that needs them, and document the access pattern in the migration.
- Store timestamps as UTC ISO strings or integer epoch milliseconds. Pick one per project and do not mix.
- Use foreign keys and `ON DELETE` rules intentionally. Do not rely on application code for referential cleanup.

Reason: SQLite is reliable when schema history is boring, explicit, and easy to replay.

## Component Patterns

- Default to Server Components for data loading and page assembly.
- Use Client Components only for browser state, event handlers, optimistic UI, or client-only APIs.
- Keep forms small: validation schema, action call, pending state, and error display should be visible in one place.
- Pass plain serializable props from server to client. Do not pass database rows with unused fields.
- Prefer composition over global state. Start with URL state for filters and tabs.

Reason: the App Router works best when server and client responsibilities are deliberately separated.

## Data Access Rules

- Pages call feature-level query functions; they do not write SQL inline.
- Query functions accept typed input objects, not loose positional arguments.
- Authorization checks happen before database mutations and again inside shared mutation helpers when reused.
- Return view models from feature queries instead of leaking raw persistence details into UI.
- Log mutation failures with stable operation names, not user-provided text.

Reason: data ownership stays local to the feature while auth and logging remain consistent.

## Dev Commands

- `npm run dev`: Start the app.
- `npm run lint`: Run linting and type-aware checks.
- `npm run test`: Run unit tests.
- `npm run db:migrate`: Apply local migrations.
- `npm run db:studio`: Inspect the local database if the project provides a studio tool.

If a command does not exist yet, add it before depending on it in documentation or automation.

## What We Do Not Do

- Do not put secrets in `.env.example`; use safe placeholders only.
- Do not call third-party services directly from Client Components.
- Do not add a global state library for server data that can be represented by URL state or server queries.
- Do not create generic `utils.ts` dumping grounds. Put helpers beside the feature or in a named `lib` module.
- Do not hide database writes behind ambiguous names like `handleSubmit` or `processData`.
- Do not weaken TypeScript to move faster. A failing type is usually the cheapest bug report.

## Review Checklist

- Does every mutation have validation, authorization, and a transaction if multiple tables are touched?
- Does every new table or query have the index it needs?
- Are Client Components limited to interactive boundaries?
- Can a new contributor find the feature's queries, actions, and schema without searching the whole repo?
- Can the app boot from a clean checkout using only the documented commands?
