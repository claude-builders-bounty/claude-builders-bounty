# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file gives Claude Code the default operating rules for a greenfield SaaS built with **Next.js 15 App Router**, **TypeScript**, **React Server Components**, **SQLite**, and either **better-sqlite3** for local/server deployments or **Turso/libSQL** for hosted SQLite.

Use this as the first context file in the repo. Prefer small, typed, testable changes over clever abstractions.

---

## 1. Stack and Versions

- **Framework:** Next.js 15 with App Router under `app/`.
- **Language:** TypeScript with `strict` mode enabled.
- **UI:** React Server Components by default; Client Components only when browser state, effects, refs, or event handlers are required.
- **Database:** SQLite.
  - Use `better-sqlite3` for local-first apps, self-hosted apps, background jobs, and simple single-region deployments.
  - Use Turso/libSQL when the app needs hosted SQLite, branching, replicas, or serverless-friendly remote access.
- **Migrations:** SQL files committed to the repo. The database schema is source-controlled, not inferred from production.
- **Validation:** Zod at all trust boundaries: route handlers, server actions, webhooks, form submissions, and environment variables.
- **Styling:** Tailwind CSS or plain CSS modules. Do not introduce a component library unless the project already uses one.
- **Testing:** Unit tests for pure logic; integration tests for database reads/writes; minimal Playwright smoke tests for critical user flows.

Reason: this stack keeps the app understandable, deployable, and easy for Claude Code to modify without hidden framework conventions.

---

## 2. Project Structure

Use this folder structure unless the user explicitly asks for a different one:

```txt
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
  api/
    health/route.ts
  layout.tsx
  globals.css
components/
  ui/
  forms/
  layout/
features/
  billing/
  auth/
  teams/
lib/
  db/
    client.ts
    schema.sql
    migrate.ts
    migrations/
      0001_initial.sql
  env.ts
  auth.ts
  errors.ts
  utils.ts
server/
  actions/
  queries/
  mutations/
tests/
  unit/
  integration/
scripts/
  migrate.ts
  seed.ts
```

Rules:

- `app/` contains routes, layouts, loading states, metadata, and route handlers only.
- `components/` contains reusable presentation components. Components must not import database clients directly.
- `features/` groups domain-specific UI and helpers when a feature grows beyond one route.
- `server/queries/` contains read-only database functions.
- `server/mutations/` contains write functions and transaction logic.
- `server/actions/` contains Server Actions that validate input, call mutations, and return serializable results.
- `lib/db/` is the only place that creates database clients, loads schema, or runs migrations.
- `lib/env.ts` is the only place that reads `process.env` directly.

Reason: keeping routes thin and database access centralized prevents accidental client-side database imports and makes changes easier to review.

---

## 3. Naming Conventions

- Files and folders: `kebab-case`, except React components which use `PascalCase.tsx`.
- React components: `PascalCase`.
- Server Actions: `verbNounAction`, for example `createWorkspaceAction`.
- Query functions: `getNoun`, `listNouns`, or `findNounByField`.
- Mutation functions: `createNoun`, `updateNoun`, `deleteNoun`, or domain verbs like `inviteMember`.
- Database tables: `snake_case` plural nouns, for example `users`, `workspaces`, `workspace_members`.
- Database columns: `snake_case`, with timestamps named `created_at`, `updated_at`, and `deleted_at`.
- IDs: use text IDs in application code. Prefer `uuid`, `ulid`, or provider IDs stored as `TEXT`.
- Boolean columns: prefix with `is_`, `has_`, or `can_`.

Reason: consistent naming lets Claude infer where code belongs and reduces accidental duplicate concepts.

---

## 4. Development Commands

Assume these scripts exist in `package.json`. If missing, add them before using them:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:seed": "tsx scripts/seed.ts"
  }
}
```

Before proposing a PR, run:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

If the repo uses `pnpm`, `bun`, or `yarn`, keep the existing package manager. Do not switch package managers.

Reason: typecheck catches most App Router and Server Action mistakes before runtime.

---

## 5. Environment Variables

All environment variables must be declared and validated in `lib/env.ts`:

```ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env` outside `lib/env.ts`.
- Prefix browser-exposed variables with `NEXT_PUBLIC_` only when they are safe to expose.
- Keep `.env.example` updated whenever a required variable is added.
- Do not commit real secrets.

Reason: centralized validation fails fast and prevents production deployments with missing configuration.

---

## 6. SQLite and Migration Conventions

### Schema Ownership

- Store canonical schema in `lib/db/schema.sql`.
- Store incremental migrations in `lib/db/migrations/`.
- Migrations are append-only once merged. Do not edit historical migrations except before the first release.
- Each migration filename must start with a zero-padded sequence number: `0001_initial.sql`, `0002_add_workspace_members.sql`.

### SQL Style

Use explicit constraints:

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

Rules:

- Enable foreign keys for every SQLite connection: `PRAGMA foreign_keys = ON;`.
- Use `TEXT` timestamps in ISO-8601 format unless the existing schema uses another convention.
- Use transactions for multi-step writes.
- Add indexes for foreign keys and frequently filtered columns.
- Keep SQL readable. Do not hide important schema changes inside ORM magic.
- If using Turso/libSQL, keep SQL portable and avoid local-only SQLite extensions unless documented.

Reason: SQLite is reliable when constraints and migrations are explicit; implicit schema generation is harder to audit.

### Database Client

`lib/db/client.ts` owns the connection:

```ts
import Database from "better-sqlite3";
import { env } from "@/lib/env";

const db = new Database(env.DATABASE_URL);
db.pragma("foreign_keys = ON");
db.pragma("journal_mode = WAL");

export { db };
```

For Turso/libSQL, expose one typed client from the same file and keep calling code unchanged where possible.

Reason: one client module makes it easy to swap `better-sqlite3` for Turso later.

---

## 7. Data Access Patterns

Use thin routes and typed server functions.

### Query Example

```ts
// server/queries/get-user.ts
import { db } from "@/lib/db/client";

export type User = {
  id: string;
  email: string;
  name: string | null;
};

export function getUserById(id: string): User | null {
  return db.prepare("SELECT id, email, name FROM users WHERE id = ?").get(id) as User | undefined ?? null;
}
```

### Mutation Example

```ts
// server/mutations/create-user.ts
import { randomUUID } from "node:crypto";
import { db } from "@/lib/db/client";

export function createUser(input: { email: string; name?: string }) {
  const id = randomUUID();

  db.prepare(`
    INSERT INTO users (id, email, name)
    VALUES (?, ?, ?)
  `).run(id, input.email.toLowerCase(), input.name ?? null);

  return { id };
}
```

Rules:

- Parameterize all SQL. Never concatenate user input into SQL strings.
- Return plain serializable objects from server functions.
- Keep authorization checks close to the mutation or query that needs them.
- Prefer explicit selected columns over `SELECT *`.
- Do not call mutations from Client Components. Use Server Actions or Route Handlers.

Reason: explicit queries are easier to inspect, safer against SQL injection, and friendlier to small SaaS codebases than over-abstracted repositories.

---

## 8. App Router and Component Patterns

### Server Components by Default

Use Server Components for pages that fetch data:

```tsx
// app/(app)/dashboard/page.tsx
import { listProjectsForCurrentUser } from "@/server/queries/list-projects";

export default async function DashboardPage() {
  const projects = await listProjectsForCurrentUser();

  return <ProjectList projects={projects} />;
}
```

### Client Components Only When Needed

Add `"use client"` only for components that need browser-only behavior:

```tsx
"use client";

import { useState } from "react";

export function RenameProjectForm() {
  const [name, setName] = useState("");
  return <input value={name} onChange={(event) => setName(event.target.value)} />;
}
```

Rules:

- Do not add `"use client"` to a full page unless unavoidable.
- Pass data from Server Components into Client Components as serializable props.
- Do not import `server/`, `lib/db/`, or Node-only modules into Client Components.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` when routes need clear states.
- Use `metadata` exports for SEO and page titles.

Reason: Server Components keep bundles small and avoid leaking server-only code to the browser.

---

## 9. Server Actions and Forms

Server Actions must validate input and return predictable results.

```ts
// server/actions/create-project-action.ts
"use server";

import { z } from "zod";
import { createProject } from "@/server/mutations/create-project";

const schema = z.object({
  name: z.string().min(1).max(80),
});

export async function createProjectAction(formData: FormData) {
  const parsed = schema.safeParse({
    name: formData.get("name"),
  });

  if (!parsed.success) {
    return { ok: false, error: "Invalid project name" } as const;
  }

  const project = createProject(parsed.data);
  return { ok: true, project } as const;
}
```

Rules:

- Validate every Server Action input with Zod.
- Return discriminated results like `{ ok: true }` or `{ ok: false, error }`.
- Revalidate affected paths or tags after successful mutations.
- Never trust hidden form fields for authorization decisions.

Reason: Server Actions are public entry points and must be treated like API endpoints.

---

## 10. Authentication and Authorization

- Keep authentication helpers in `lib/auth.ts`.
- Keep route protection in server-side checks, not only middleware.
- Middleware may redirect obvious unauthenticated page visits, but mutations and queries must still enforce authorization.
- Model team membership explicitly with a join table, for example `workspace_members`.
- Use role names that map to product behavior: `owner`, `admin`, `member`, `viewer`.

Rules:

- Never authorize based only on client-provided IDs.
- Every mutation that touches workspace data must verify current user membership.
- Prefer small authorization helpers such as `requireUser()` and `requireWorkspaceRole()`.

Reason: SaaS bugs often come from trusting the route or UI instead of checking permissions at the data boundary.

---

## 11. Error Handling

- Use typed application errors in `lib/errors.ts`.
- Show user-safe messages in UI and logs with technical details on the server.
- Do not expose database errors, stack traces, SQL strings, or secrets to the browser.
- Return `404` for resources the user cannot access when revealing existence would leak information.

Reason: predictable errors make the app safer and easier to debug.

---

## 12. Testing Standards

Write tests at the level where the bug could happen:

- Pure utilities: unit tests.
- SQL queries and mutations: integration tests against a temporary SQLite database.
- Critical flows such as signup, login, billing checkout, and dashboard access: Playwright smoke tests.

For database tests:

- Use a fresh temporary database per test file or test case.
- Run migrations before assertions.
- Assert constraints, not only happy paths.

Required checks before PR:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

### Greenfield Validation / Smoke Test

When adding this file to a new project, verify that Claude Code can use it without extra architectural clarification:

1. Create a fresh Next.js 15 App Router project with TypeScript.
2. Add SQLite using either `better-sqlite3` or Turso/libSQL.
3. Place this file at the repository root as `CLAUDE.md`.
4. Ask Claude Code:

```text
Add a workspace invite feature with SQLite migrations, server actions, authorization checks, and tests.
```

Expected behavior:

- Claude identifies the involved route, Server Action, mutation, query, schema, migration, and test files before editing.
- Claude keeps database access in `lib/db/`, `server/queries/`, or `server/mutations/`.
- Claude adds a numbered SQL migration instead of editing historical migrations.
- Claude validates input with Zod and checks workspace membership server-side.
- Claude proposes or runs `typecheck`, `lint`, `test`, and `build` before summarizing the change.

Reason: this smoke test confirms the file is actionable as Claude Code context, not just a static style guide.

Reason: SQLite integration tests are cheap and catch schema drift before deployment.

---

## 13. Security Rules

- Parameterize SQL. No string-concatenated SQL with user input.
- Validate all external input with Zod.
- Keep secrets server-only.
- Add CSRF protection for cookie-authenticated mutations if the auth setup does not already provide it.
- Verify webhook signatures before parsing business payloads.
- Rate-limit auth endpoints, invitation flows, and expensive AI/API routes.
- Sanitize user-generated HTML or render it as plain text.

Reason: small SaaS apps fail through boring security mistakes, not exotic attacks.

---

## 14. Performance Rules

- Avoid unnecessary Client Components.
- Avoid N+1 database queries in Server Components.
- Add indexes before adding caching for slow queries.
- Use pagination for lists that can grow beyond 100 rows.
- Cache read-only marketing content; be careful caching user-specific dashboard data.

Reason: SQLite performs well when queries are explicit and indexed.

---

## 15. What We Do Not Do

- Do not introduce Prisma, Drizzle, tRPC, Redux, GraphQL, or a UI framework unless requested or already present.
  - Reason: this template is intentionally small and SQL-first.
- Do not convert Server Components to Client Components to fix type errors.
  - Reason: that hides architecture problems and increases bundle size.
- Do not create generic `utils.ts` dumping grounds for domain logic.
  - Reason: domain code belongs in `features/`, `server/queries/`, or `server/mutations/`.
- Do not edit old migrations after they are merged.
  - Reason: production databases need a stable migration history.
- Do not add environment variables without updating `.env.example` and `lib/env.ts`.
  - Reason: deployments should fail before runtime, not during user requests.
- Do not swallow errors with empty `catch` blocks.
  - Reason: silent failures make billing, auth, and data corruption bugs hard to find.

---

## 16. How Claude Code Should Work in This Repo

When asked to make a change:

1. Identify the route, feature, query, mutation, and schema files involved.
2. Check whether the change needs a migration.
3. Keep database access in `server/queries/`, `server/mutations/`, or `lib/db/`.
4. Validate new inputs with Zod.
5. Add or update tests at the right level.
6. Run typecheck, lint, tests, and build.
7. Summarize changed files, behavior, and verification commands.

When uncertain:

- Prefer asking one precise question over making architectural assumptions.
- If the existing repo already has a pattern, follow it even if this file suggests a different default.
- Do not perform destructive database operations without explicit user approval.

Reason: this workflow keeps generated changes small, reviewable, and safe for production SaaS work.
