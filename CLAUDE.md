# CLAUDE.md - Next.js 15 + SQLite SaaS Template

This file is the project contract for a greenfield SaaS built with Next.js 15 App Router, TypeScript, SQLite, better-sqlite3, and Drizzle ORM. Follow it exactly unless a product requirement forces a change, and document that change in the pull request.

## Stack & Versions

- **Next.js 15 App Router**: use the `app/` directory, Server Components by default, Route Handlers for HTTP integrations, and Server Actions for form-backed mutations. App Router keeps data loading close to routes and avoids a separate client API layer for normal product workflows.
- **React 19**: use modern React primitives and keep client components small. React 19 pairs with Next.js 15 and improves server/client composition.
- **TypeScript strict mode**: `strict: true`, `noUncheckedIndexedAccess: true`, and `exactOptionalPropertyTypes: true`. SaaS bugs usually come from unclear nullability and unchecked request data; the compiler should catch those.
- **SQLite with better-sqlite3**: use local file-backed SQLite for simple deployment, deterministic tests, and low operational overhead. `better-sqlite3` is synchronous by design, which matches SQLite's single-file behavior and avoids fake async wrappers.
- **Drizzle ORM**: use Drizzle for typed schema, migrations, and query builders. It stays close to SQL while preventing stringly typed table access.
- **Zod**: validate environment variables, form data, URL params, and external payloads at boundaries. TypeScript is not runtime validation.
- **Vitest and React Testing Library**: use Vitest for fast unit tests and component behavior tests. Keep Playwright only for critical end-to-end flows.
- **pnpm**: use pnpm for deterministic installs and fast local workflows. Do not mix package managers.

Expected package family:

```json
{
  "next": "^15.0.0",
  "react": "^19.0.0",
  "react-dom": "^19.0.0",
  "typescript": "^5.6.0",
  "better-sqlite3": "^11.0.0",
  "@types/better-sqlite3": "^7.6.0",
  "drizzle-orm": "^0.36.0",
  "drizzle-kit": "^0.27.0",
  "tsx": "^4.19.0",
  "zod": "^3.23.0",
  "vitest": "^2.1.0",
  "@testing-library/react": "^16.0.0",
  "@testing-library/jest-dom": "^6.6.0",
  "eslint": "^9.0.0",
  "eslint-config-next": "^15.0.0"
}
```

Use newer patch or minor versions when creating the project, but keep the same stack unless this file is intentionally revised.

## Dev Commands

Use these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx src/db/migrate.ts",
    "db:studio": "drizzle-kit studio",
    "check": "pnpm lint && pnpm typecheck && pnpm test"
  }
}
```

Run `pnpm check` before opening a PR because it is the smallest command that catches lint, type, and unit-level regressions.

## Project Structure

Use this layout:

```text
.
├── drizzle/
│   └── migrations/
├── public/
├── src/
│   ├── app/
│   │   ├── (app)/
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx
│   │   ├── (auth)/
│   │   │   ├── sign-in/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx
│   │   ├── api/
│   │   │   └── webhooks/
│   │   │       └── stripe/
│   │   │           └── route.ts
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/
│   │   └── feature-name/
│   ├── db/
│   │   ├── client.ts
│   │   ├── migrate.ts
│   │   └── schema.ts
│   ├── features/
│   │   └── billing/
│   │       ├── actions.ts
│   │       ├── data.ts
│   │       ├── schemas.ts
│   │       └── tests/
│   ├── lib/
│   │   ├── env.ts
│   │   ├── errors.ts
│   │   └── utils.ts
│   └── test/
│       └── setup.ts
├── .env.example
├── drizzle.config.ts
├── next.config.ts
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

Reasons:

- `src/app` owns routing only. Business logic does not live in route files.
- `src/features/<feature>` owns use-case code: actions, reads, validation schemas, and tests for one product area.
- `src/components/ui` contains reusable primitives. Feature-specific components stay under `components/feature-name` or inside the feature folder when tightly coupled.
- `src/db` is the only place that imports `better-sqlite3` or defines Drizzle tables.
- `src/lib` is for cross-cutting utilities. If a helper only serves one feature, keep it in that feature.

## Naming Conventions

- Files and folders use kebab-case: `billing-summary.tsx`, `create-checkout-session.ts`.
- React components use PascalCase exports: `BillingSummary`.
- Server Actions are named as commands: `createWorkspaceAction`, `updatePlanAction`.
- Database tables use plural snake_case names: `users`, `workspaces`, `workspace_members`.
- Database columns use snake_case: `created_at`, `workspace_id`.
- TypeScript variables use camelCase, including mapped database fields after query boundaries.
- Zod schemas end with `Schema`: `createWorkspaceSchema`.
- Tests sit beside the feature they cover and use `.test.ts` or `.test.tsx`.

Consistent names reduce translation work when moving from UI to action to schema to database.

## Database Conventions

Define all tables in `src/db/schema.ts`:

```ts
import { sql } from "drizzle-orm";
import { integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const workspaces = sqliteTable(
  "workspaces",
  {
    id: text("id").primaryKey(),
    ownerId: text("owner_id").notNull(),
    name: text("name").notNull(),
    slug: text("slug").notNull(),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`(unixepoch())`),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .default(sql`(unixepoch())`)
  },
  (table) => ({
    slugIdx: uniqueIndex("workspaces_slug_idx").on(table.slug)
  })
);
```

Use a singleton database client in `src/db/client.ts`:

```ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { env } from "@/lib/env";
import * as schema from "./schema";

const sqlite = new Database(env.DATABASE_URL);
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite, { schema });
```

Rules:

- Generate migrations with `pnpm db:generate`; do not hand-write migration SQL unless Drizzle cannot express the change.
- Commit generated migration files. The application must not depend on runtime schema synchronization.
- Migrations are append-only after merge. If a merged migration is wrong, add a corrective migration.
- Always enable foreign keys. SQLite does not enforce them unless `PRAGMA foreign_keys = ON` is set.
- Use transactions for multi-table writes. Partial writes create support incidents.
- Store timestamps as SQLite integer timestamps through Drizzle's timestamp mode.
- Do not import `db` into Client Components.

Migration runner:

```ts
// src/db/migrate.ts
import Database from "better-sqlite3";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { env } from "@/lib/env";

const sqlite = new Database(env.DATABASE_URL);
const db = drizzle(sqlite);

migrate(db, { migrationsFolder: "drizzle/migrations" });
sqlite.close();
```

## Environment Setup

Create `.env.example`:

```bash
DATABASE_URL="./data/app.db"
APP_URL="http://localhost:3000"
SESSION_SECRET="replace-with-at-least-32-random-characters"
```

Validate env vars in `src/lib/env.ts`:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  APP_URL: z.string().url(),
  SESSION_SECRET: z.string().min(32)
});

export const env = envSchema.parse(process.env);
```

Rules:

- Read `process.env` only in `src/lib/env.ts`.
- Add every required variable to `.env.example`.
- Validate secrets by shape, not by checking for production values.

## Component Patterns

Server Components are the default:

```tsx
import { getWorkspace } from "@/features/workspaces/data";

export default async function DashboardPage() {
  const workspace = await getWorkspace();
  return <h1>{workspace.name}</h1>;
}
```

Use Client Components only for browser state, event handlers, refs, animations, or browser-only APIs:

```tsx
"use client";

import { useState } from "react";

export function WorkspaceNameInput({ defaultValue }: { defaultValue: string }) {
  const [value, setValue] = useState(defaultValue);
  return <input value={value} onChange={(event) => setValue(event.target.value)} />;
}
```

Rules:

- Keep `use client` files leaf-level when possible. A top-level client boundary ships too much JavaScript.
- Pass plain serializable props from Server Components to Client Components.
- Fetch database data in Server Components or feature data functions, not in `useEffect`.
- Prefer composition over global stores. Most SaaS screens are route-driven, not app-state-driven.

## Server Actions

Use Server Actions for form submissions and authenticated product mutations:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db } from "@/db/client";
import { workspaces } from "@/db/schema";
import { requireUser } from "@/features/auth/session";

const createWorkspaceSchema = z.object({
  name: z.string().trim().min(2).max(80)
});

export async function createWorkspaceAction(formData: FormData) {
  const user = await requireUser();
  const input = createWorkspaceSchema.parse({
    name: formData.get("name")
  });

  await db.insert(workspaces).values({
    id: crypto.randomUUID(),
    ownerId: user.id,
    name: input.name,
    slug: input.name.toLowerCase().replaceAll(" ", "-")
  });

  revalidatePath("/dashboard");
}
```

Rules:

- Validate all action inputs with Zod.
- Check authentication and authorization inside the action or in a feature helper called by the action.
- Return small typed results for recoverable form errors. Throw for unexpected errors.
- Call `revalidatePath` or `revalidateTag` after writes that affect rendered data.

## API Routes

Use Route Handlers for:

- Webhooks from third-party services.
- Public machine-to-machine endpoints.
- File uploads that need request streaming.
- Endpoints consumed by external clients.

Use Server Actions for:

- Internal forms.
- Button-triggered mutations.
- Authenticated dashboard updates.

Reason: Route Handlers are an HTTP boundary. Server Actions are a product UI mutation boundary. Keeping that distinction avoids building an unnecessary internal REST API.

Webhook example:

```ts
// src/app/api/webhooks/stripe/route.ts
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const rawBody = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "Missing signature" }, { status: 400 });
  }

  // Verify signature with rawBody and dispatch the event in a feature module.
  return NextResponse.json({ received: true });
}
```

## Data Access Patterns

- Put reads in `features/<feature>/data.ts`.
- Put mutations in `features/<feature>/actions.ts` when called by UI.
- Keep SQL-shaped logic out of components.
- Return domain-shaped objects from data functions; do not leak Drizzle query details across the app.
- Use explicit selected columns for list views. Selecting entire rows makes future schema changes expensive.

Example:

```ts
import { asc, eq } from "drizzle-orm";
import { db } from "@/db/client";
import { workspaces } from "@/db/schema";

export async function listWorkspacesForUser(userId: string) {
  return db
    .select({
      id: workspaces.id,
      name: workspaces.name,
      slug: workspaces.slug
    })
    .from(workspaces)
    .where(eq(workspaces.ownerId, userId))
    .orderBy(asc(workspaces.name));
}
```

## Testing Patterns

Use Vitest for pure logic, validation, and feature data behavior.

Validation test:

```ts
import { describe, expect, it } from "vitest";
import { createWorkspaceSchema } from "../schemas";

describe("createWorkspaceSchema", () => {
  it("trims and accepts a valid workspace name", () => {
    const result = createWorkspaceSchema.parse({ name: " Acme " });
    expect(result.name).toBe("Acme");
  });
});
```

Component test:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BillingSummary } from "../billing-summary";

describe("BillingSummary", () => {
  it("shows the current plan", () => {
    render(<BillingSummary planName="Pro" />);
    expect(screen.getByText("Pro")).toBeInTheDocument();
  });
});
```

Rules:

- Test schemas and permission checks directly because they protect the app boundary.
- Test Server Actions through the feature behavior they trigger when possible.
- Use temporary SQLite databases for database tests. Do not point tests at development data.
- Do not snapshot full pages. Snapshots hide behavior and create noisy diffs.

## Git Conventions

- Branch names: `feature/billing-portal`, `fix/session-expiry`, `chore/update-drizzle`.
- Commit format: `type(scope): summary`, for example `feat(billing): add checkout action`.
- Use these types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
- Keep PRs focused on one product or infrastructure change.
- Include migration files in the same PR as the schema change.

Reason: predictable history makes production debugging and migration review easier.

## What We Do Not Do

- **No Prisma**: Prisma adds a heavier client and migration layer than this stack needs. Drizzle keeps SQLite usage explicit and lightweight.
- **No tRPC by default**: App Router and Server Actions already provide typed server/client workflows for internal UI. Add tRPC only when there is a real multi-client API need.
- **No Pages Router**: mixing routing systems creates duplicated conventions and confusing data-fetching rules.
- **No client-side database calls**: SQLite belongs on the server. Client code talks through rendered data, Server Actions, or Route Handlers.
- **No global state for server data**: server data belongs in Server Components and cache-aware data functions. Use client state only for local interaction.
- **No unvalidated inputs**: every form, route param, search param, webhook, and env var crosses a trust boundary.
- **No runtime schema push in production**: production changes go through committed migrations.
- **No hidden package manager changes**: do not add `package-lock.json` or `yarn.lock`.

## Anti-Patterns

Do not do this:

```tsx
"use client";

export default function DashboardPage() {
  useEffect(() => {
    fetch("/api/workspaces");
  }, []);

  return null;
}
```

Reason: this ships unnecessary JavaScript, delays data loading, and creates an internal API route that Server Components do not need.

Do not do this:

```ts
const name = formData.get("name") as string;
await db.insert(workspaces).values({ name });
```

Reason: type assertions do not validate runtime data. Use Zod before writing.

Do not do this:

```ts
await db.run(sql`ALTER TABLE users ADD COLUMN plan text`);
```

Reason: ad hoc schema changes bypass migration history and make deploys unreproducible.

Do not do this:

```ts
export const everything = await db.select().from(workspaces);
```

Reason: module-level database reads run at import time and are hard to cache, test, and invalidate.

Do not do this:

```ts
import { db } from "@/db/client";

export function ClientWidget() {
  return null;
}
```

Reason: importing server-only modules into client boundaries can break builds and leak implementation details.

Do not do this:

```ts
export async function GET() {
  return Response.json(await db.select().from(users));
}
```

Reason: returning raw rows leaks internal columns. Select and shape explicit response fields.

Do not do this:

```ts
process.env.DATABASE_URL!
```

Reason: non-null assertions hide missing configuration. Use the validated `env` module.

## Pull Request Checklist

- `pnpm check` passes.
- Database changes include generated migrations.
- New inputs are validated with Zod.
- New mutations enforce authorization.
- Server Components remain server-side unless browser behavior is required.
- `.env.example` is updated for new environment variables.
- Tests cover risky validation, permissions, or data behavior.
