# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file gives Claude Code the project rules for a production-minded SaaS built with **Next.js 15 App Router**, **TypeScript**, **SQLite**, and either **better-sqlite3** for local/server deployments or **Turso/libSQL** for hosted edge-friendly deployments.

The goal is not generic advice. Follow these conventions unless a task explicitly says otherwise.

## Stack and versions

- Runtime: Node.js 20 LTS or newer.
- Framework: Next.js 15 with App Router only.
- Language: TypeScript in `strict` mode.
- Styling: Tailwind CSS plus small local component primitives.
- Database: SQLite.
  - Default local adapter: `better-sqlite3`.
  - Hosted adapter: Turso/libSQL when the deployment target cannot write to a local SQLite file.
- Validation: Zod for runtime parsing at every trust boundary.
- Auth/session: cookie-based sessions; keep auth server-only.
- Testing: Vitest for units, Playwright for browser flows when present.

Why: this stack keeps the app easy to run locally, cheap to deploy, and explicit about server/client boundaries.

## Non-negotiable architecture rules

1. Server data access belongs in server-only modules under `src/server/**`.
2. Client components are only for interactivity; they must not import database, auth, or filesystem modules.
3. SQL migrations are append-only. Never edit a migration that has been committed.
4. Every mutation validates input with Zod before touching the database.
5. Every page that reads private user data must verify the session on the server.
6. Prefer simple server actions and route handlers over introducing extra API layers.
7. Keep business rules out of React components.
8. Use explicit SQL and small repository functions; do not hide behavior behind magic ORMs unless the project already uses one.

## Expected folder structure

Use this structure for greenfield work:

```text
src/
  app/
    (marketing)/
      page.tsx
      pricing/page.tsx
    (app)/
      dashboard/page.tsx
      settings/page.tsx
      layout.tsx
    api/
      health/route.ts
      webhooks/
        stripe/route.ts
    actions/
      account.ts
      billing.ts
    layout.tsx
    globals.css
  components/
    ui/
    forms/
    layout/
  features/
    billing/
      billing.schema.ts
      billing.service.ts
      billing.types.ts
    projects/
      project.schema.ts
      project.service.ts
      project.types.ts
  lib/
    env.ts
    result.ts
    dates.ts
    ids.ts
  server/
    auth/
      session.ts
      password.ts
    db/
      connection.ts
      migrate.ts
      schema.sql
      migrations/
        0001_initial.sql
    repositories/
      users.ts
      projects.ts
  test/
    fixtures/
    helpers/
```

Rules:

- `src/app/**` wires routing and rendering.
- `src/features/**` contains domain logic and schemas.
- `src/server/**` contains server-only integrations: database, auth, secrets, payment webhooks.
- `src/components/**` contains reusable UI only; no direct database calls.
- `src/lib/**` contains pure utilities safe to import from server or client unless named otherwise.

Why: this separation lets Claude edit features without accidentally leaking secrets into client bundles.

## Server vs client component rules

- Components are server components by default.
- Add `'use client'` only when the file needs browser state, effects, DOM APIs, or event handlers.
- A client component may receive serialized data from a server component but must not fetch private data itself.
- Never import from `src/server/**` inside a client component.
- Place interactive form widgets in `src/components/forms/**`; keep the mutation in a server action.

Good pattern:

```tsx
// Server component
import { listProjectsForUser } from '@/server/repositories/projects';
import { ProjectPicker } from '@/components/forms/project-picker';

export default async function DashboardPage() {
  const projects = await listProjectsForUser();
  return <ProjectPicker projects={projects} />;
}
```

Bad pattern:

```tsx
'use client';
import { db } from '@/server/db/connection'; // never do this
```

## Naming conventions

- Files: kebab-case (`project-card.tsx`, `create-project-form.tsx`).
- React components: PascalCase.
- Server actions: verb-object names (`createProject`, `updateBillingEmail`).
- Database tables: snake_case plural (`users`, `project_members`).
- Columns: snake_case (`created_at`, `billing_customer_id`).
- Zod schemas: `CreateProjectInput`, `UpdateAccountInput`.
- Repository methods: action-oriented and explicit (`findUserByEmail`, `insertProject`, `listProjectsForUser`).

Why: consistent names make it obvious whether code is UI, validation, persistence, or domain logic.

## Environment variables

Create a typed environment module at `src/lib/env.ts`:

```ts
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Only variables prefixed with `NEXT_PUBLIC_` may be used in client components.
- Do not read `process.env` throughout the codebase; import `env`.
- Add new required variables to `.env.example` in the same change.

## SQLite connection rules

For `better-sqlite3`, keep one shared server-only connection:

```ts
// src/server/db/connection.ts
import 'server-only';
import Database from 'better-sqlite3';
import { env } from '@/lib/env';

export const db = new Database(env.DATABASE_URL.replace('file:', ''));
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
```

Rules:

- Enable `foreign_keys` on every connection.
- Use WAL mode for local file databases.
- Keep prepared statements close to repository functions.
- Do not open SQLite connections in React components.
- For Turso/libSQL, isolate the client behind the same repository interface where practical.

Why: SQLite is reliable when connection behavior and constraints are explicit.

## SQL and migration conventions

Migration files live in `src/server/db/migrations/` and are named:

```text
0001_initial.sql
0002_add_project_members.sql
0003_add_billing_customer_id.sql
```

Rules:

1. Migrations are append-only after commit.
2. Every table has:
   - `id TEXT PRIMARY KEY`
   - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
   - `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP` when records are mutable.
3. Use ISO timestamp text unless the existing project uses Unix integers.
4. Add indexes for foreign keys and common lookup columns.
5. Use `ON DELETE CASCADE` only for true ownership relationships.
6. Prefer explicit constraints over application-only checks.
7. Wrap multi-step migrations in a transaction when the migration runner supports it.

Example:

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_owner_id ON projects(owner_id);
```

Why: future Claude sessions need deterministic schema history and safe rollback reasoning.

## Data access pattern

Repository files own SQL. Services own business rules.

```ts
// src/server/repositories/projects.ts
import 'server-only';
import { db } from '@/server/db/connection';

export function findProjectBySlug(slug: string) {
  return db.prepare('SELECT * FROM projects WHERE slug = ?').get(slug);
}
```

```ts
// src/features/projects/project.service.ts
import { createProjectInput } from './project.schema';
import { insertProject } from '@/server/repositories/projects';

export async function createProjectForUser(rawInput: unknown, userId: string) {
  const input = createProjectInput.parse(rawInput);
  return insertProject({ ...input, ownerId: userId });
}
```

Rules:

- Do not concatenate SQL strings with user input.
- Prefer parameter binding for every value.
- Keep transaction boundaries in services when the operation spans multiple repositories.
- Return plain objects, not database driver internals.

## Server actions and route handlers

Use server actions for app-owned form mutations. Use route handlers for webhooks, health checks, and external API consumers.

Server action rules:

- Start action files with `'use server'`.
- Validate inputs with Zod.
- Verify the session before mutations.
- Return a typed result object instead of throwing for expected validation errors.
- Call `revalidatePath` or `revalidateTag` after successful mutations.

```ts
'use server';

import { revalidatePath } from 'next/cache';
import { z } from 'zod';
import { requireUser } from '@/server/auth/session';
import { createProjectForUser } from '@/features/projects/project.service';

const inputSchema = z.object({ name: z.string().min(2).max(80) });

export async function createProjectAction(formData: FormData) {
  const user = await requireUser();
  const parsed = inputSchema.safeParse({ name: formData.get('name') });
  if (!parsed.success) return { ok: false, error: 'Invalid project name' } as const;

  await createProjectForUser(parsed.data, user.id);
  revalidatePath('/dashboard');
  return { ok: true } as const;
}
```

Route handler rules:

- Validate request body and headers.
- Keep webhook signature verification before JSON parsing when the provider requires raw body.
- Return explicit status codes.

## Authentication and authorization

- `requireUser()` is the only allowed helper for pages/actions that require login.
- `getCurrentUser()` may return `null` for optional auth.
- Authorization checks must happen server-side near the data access.
- Never trust `userId`, `role`, or `teamId` from client input.
- Store password hashes only when first-party auth is required; use Argon2id or bcrypt with strong cost.
- Use `httpOnly`, `secure`, `sameSite=lax` cookies for sessions.

Why: SaaS bugs usually come from trusting IDs passed from the browser.

## Forms and validation

- Define Zod schemas next to the feature (`src/features/<feature>/<feature>.schema.ts`).
- Reuse schemas in server actions and route handlers.
- Keep form state serializable.
- Show field-level errors where possible.
- Do not duplicate validation rules manually in components unless they are only for UX hints.

## UI and component patterns

- Keep base components small and accessible.
- Use semantic HTML first.
- Use Tailwind utilities directly for one-off layouts.
- Extract components only when reused or when a file becomes hard to scan.
- Server components fetch data; client components manage interaction.
- Prefer composition over global state.

Component checklist:

- Keyboard accessible.
- Loading and empty states included.
- Error state included for async UI.
- No secret or server-only imports.

## Testing expectations

When adding logic:

- Unit test pure utilities and services with Vitest.
- Test repository functions against a temporary SQLite database.
- Test critical browser flows with Playwright if the project already has Playwright.
- Do not add snapshot tests for ordinary Tailwind markup.

Recommended commands:

```bash
npm run typecheck
npm run lint
npm run test
npm run test:e2e
```

If a command is missing, either add it or explain why in the PR.

## Error handling

Use a small typed result helper for expected failures:

```ts
export type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };
```

Rules:

- Expected validation/auth/business failures return typed results.
- Unexpected infrastructure failures may throw and be handled by Next.js error boundaries/logging.
- Do not expose raw database errors to users.

## Performance rules

- Fetch only the columns needed for lists.
- Add indexes before adding queries that filter by a column in production paths.
- Use pagination for unbounded lists.
- Avoid client-side fetching for initial private dashboard data.
- Use `cache`/`revalidateTag` only after confirming data is safe to cache for the user scope.

## Security rules

- Use parameterized SQL only.
- Validate every external input.
- Keep secrets in server-only modules.
- Never log session tokens, API keys, password hashes, or webhook signatures.
- Confirm destructive actions with explicit UI and server-side authorization.
- Use CSRF-safe patterns for cookie-authenticated mutations.
- Verify webhook signatures before processing provider events.

## What we do not do, and why

- Do not add a separate Express server: Next route handlers are enough for this stack.
- Do not introduce Prisma/Drizzle unless the task asks or the project already uses it: explicit SQL is easier for Claude to reason about in small SQLite SaaS apps.
- Do not put database calls in components: it breaks boundaries and makes auth harder to audit.
- Do not edit committed migrations: it corrupts other developers' databases.
- Do not create generic `utils.ts` dumping grounds: name utilities by purpose.
- Do not use `any` to bypass TypeScript errors: fix the type or narrow unknown input.
- Do not put business rules in JSX: services are testable, components are not the policy layer.
- Do not skip empty/loading/error states for user-facing pages.

## Before changing code checklist

1. Identify whether the change is UI, server action, route handler, service, repository, or migration.
2. Read the relevant feature schema and repository before editing.
3. Check whether the file is server or client.
4. Add or update tests for business logic.
5. Run typecheck, lint, and tests if available.
6. Document new environment variables or commands.

## PR checklist

- [ ] Server/client boundary is respected.
- [ ] Inputs are validated with Zod.
- [ ] SQL uses parameter binding.
- [ ] Migration is append-only and indexed where needed.
- [ ] Auth and authorization checks are server-side.
- [ ] Tests or a clear manual test note are included.
- [ ] `.env.example` is updated when env vars change.
- [ ] README or feature docs are updated when setup changes.
