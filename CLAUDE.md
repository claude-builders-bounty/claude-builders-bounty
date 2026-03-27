# CLAUDE.md

Opinionated defaults for a production-minded SaaS app built with **Next.js 15 App Router + SQLite**.

This file is written so Claude Code can start making safe changes without first asking broad setup questions.

---

## Stack & Versions

- **Framework:** Next.js 15 App Router
- **Language:** TypeScript, `strict: true`
- **Database:** SQLite via `better-sqlite3` for local/dev, or Turso/libSQL for hosted SQLite
- **ORM / SQL style:** SQL-first. Prefer explicit SQL or a thin query layer over heavy hidden ORM magic.
- **Runtime split:**
  - Server Components by default
  - Client Components only where interactivity is required
  - Route Handlers for API boundaries
  - Server Actions only for small, UI-adjacent mutations

---

## Project Structure

```text
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
  globals.css
components/
  ui/
  forms/
  app-shell/
lib/
  db/
    client.ts
    schema/
    migrations/
    queries/
    mutations/
  auth/
  billing/
  flags/
  validation/
  utils/
services/
  user/
  org/
  billing/
content/
public/
scripts/
tests/
```

### Rules

- Keep **UI routing code in `app/`** and business logic out of it.
- Put **database code under `lib/db/`**, not scattered across pages or route handlers.
- Put cross-route domain logic in **`services/`**, named by capability, not by technical layer.
- Shared presentational primitives go in **`components/ui/`**.
- If a file grows beyond one clear purpose, split it by responsibility before adding more branches.

### Why

This keeps Claude from mixing rendering, persistence, and business rules in the same file. The most common SaaS codebase failure mode is “everything happens in the route”; we do not do that.

---

## Naming Conventions

- Components: `PascalCase.tsx`
- Hooks: `useSomething.ts`
- Route handlers: `route.ts`
- Shared helpers: `kebab-case.ts`
- DB query modules: noun-based, e.g. `users.sql.ts`, `invoices.sql.ts`
- Service modules: capability-based, e.g. `create-org.ts`, `sync-subscription.ts`

### Rules

- Name files by **responsibility**, not by vague technical labels like `helpers.ts`, `misc.ts`, `temp.ts`.
- Prefer singular names for model-focused modules (`user.ts`) and verb-led names for operations (`create-user.ts`).
- Avoid `index.ts` unless it is a deliberate public barrel for a small folder.

### Why

Claude does better when filenames are semantically sharp. Ambiguous names increase wrong-file edits and duplication.

---

## Database & Migration Rules

### Core Rules

- Schema changes must go through **versioned migrations** in `lib/db/migrations/`.
- Never edit production schema by hand from app code.
- Every migration must be **forward-only** and have a clear rollback note in comments.
- Use SQLite features intentionally; do not assume PostgreSQL-only features exist.
- Store timestamps as ISO strings or unix seconds consistently; pick one and keep it global.
- Add indexes when introducing any new lookup path that will run in request time.

### Query Rules

- Read queries live in `lib/db/queries/`.
- Write queries live in `lib/db/mutations/`.
- Do not inline SQL inside React components, route handlers, or random utility files.
- If a query becomes business-policy aware, move orchestration into `services/` and keep SQL modules dumb.

### Why

SQLite stays pleasant only when schema and query discipline remain explicit. Hidden migrations and inline SQL create fragile, unreviewable changes.

---

## Component Patterns

### Default Rendering Rules

- Prefer **Server Components**.
- Add `'use client'` only when the component needs browser state, DOM APIs, or event-heavy interactivity.
- Fetch data on the server whenever possible.
- Keep client components thin; they should compose UI, not own data architecture.

### Form Rules

- Validate input at boundaries using a shared schema layer in `lib/validation/`.
- Server-side validation is mandatory even if client validation exists.
- Mutations should return structured results (`ok`, `fieldErrors`, `message`) rather than ad-hoc strings.

### Why

Most Next.js SaaS apps get worse when client components become mini-backends. Server-first keeps latency, auth, and data flow easier to reason about.

---

## Dev Commands

```bash
npm install
npm run dev
npm run test
npm run lint
```

If migrations exist, add one explicit command and keep it stable, for example:

```bash
npm run db:migrate
```

### Rules

- Do not invent new command names if an existing script already covers the job.
- Keep local setup to obvious commands. If setup needs six hidden steps, fix the setup docs instead of teaching Claude tribal knowledge.

---

## Patterns to Follow

- Prefer small pure helpers before introducing framework-heavy abstractions.
- Keep auth checks close to server boundaries.
- Return typed domain objects from services, not raw ad-hoc DB rows everywhere.
- Write the simplest thing that preserves future migration paths.
- Add tests around business rules and failure paths, not just happy-path snapshots.

---

## Anti-Patterns to Avoid

### We do not:

- Put DB access directly in React components
- Put billing logic in route handlers
- Mix validation, auth, and persistence in one giant function
- Hide critical side effects inside utility helpers with vague names
- Add generic abstraction layers “for future flexibility” before they are needed
- Use client components as the default for pages that can render on the server
- Ship schema changes without a migration artifact

### Why

These choices create the exact maintenance mess that makes Claude ask too many clarifying questions later. Clear boundaries reduce both bugs and agent confusion.

---

## What Claude Should Assume

- If unsure where business logic belongs, prefer `services/` over `app/`.
- If unsure where SQL belongs, prefer `lib/db/queries/` or `lib/db/mutations/` over inline usage.
- If adding a feature that changes stored data, look for migrations first.
- If a component needs browser-only behavior, isolate that boundary instead of promoting an entire route tree to client-side.
- If a change increases implicitness, choose the more explicit version unless the codebase already has a strong contrary pattern.

---

## Greenfield Default

If the repository is brand new and a choice is not specified elsewhere, default to:

- App Router
- TypeScript strict mode
- server-first data fetching
- SQLite with explicit migrations
- validation at every input boundary
- thin route handlers
- business logic in services
- explicit SQL/query modules

This is not the most abstract setup. It is the setup least likely to rot.
