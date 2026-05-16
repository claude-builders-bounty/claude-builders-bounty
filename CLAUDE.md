# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **Opinionated context file.** Every rule has a *why*. Follow these and Claude Code
> will produce consistent, production-ready code without needing clarifying questions.

---

## Stack & Versions

| Layer | Technology | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | RSC, streaming, server actions — best DX for full-stack apps |
| Language | TypeScript | 5.x | Strict mode. Catch bugs at compile, not runtime |
| Styling | Tailwind CSS | 4.x | Utility-first, colocation with components, zero-build |
| UI Primitives | shadcn/ui | latest (new-york style) | Copy-paste ownership, not a dependency. Accessible by default |
| Database | Turso (libsql) | latest | Distributed SQLite — edge replicas, branching, zero-downtime migrations |
| Local DB | better-sqlite3 | 9.x | Exact match for libsql dialect during development |
| ORM + Migrations | Drizzle ORM | latest | SQL-like, type-safe, lightweight. No codegen bloat |
| Auth | Better Auth | latest | Framework-native to Next.js, typed sessions, no vendor lock-in |
| Validation | Zod | 3.x | Runtime validation for server actions and API boundaries |
| Package Manager | pnpm | 9.x | Strict, fast, disk-efficient |

**Node.js**: 22 LTS. **Runtime**: Edge-compatible where possible (API routes, middleware), Node.js for DB writes.

---

## Folder Structure

```
src/
├── app/                    # App Router — file-based routing
│   ├── (marketing)/       # Route group: public pages
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/       # Route group: authenticated pages
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   └── layout.tsx      # Auth gate lives here
│   ├── api/               # API routes (only for webhooks/external callbacks)
│   │   └── webhooks/
│   │       └── stripe/
│   │           └── route.ts
│   ├── layout.tsx          # Root layout — providers, fonts
│   ├── page.tsx            # Landing page
│   └── error.tsx           # Global error boundary
├── components/
│   ├── ui/                # shadcn/ui primitives (button, card, dialog…)
│   ├── forms/             # Reusable form fields + validation wiring
│   └── [feature]/         # Feature-specific components
│       ├── [Feature]Card.tsx
│       └── [Feature]Form.tsx
├── lib/
│   ├── db/
│   │   ├── index.ts       # DB client singleton (Turso in prod, better-sqlite3 local)
│   │   └── schema.ts      # Drizzle table definitions
│   ├── auth/
│   │   ├── index.ts       # Better Auth config + exports (auth, signIn, signOut)
│   │   └── middleware.ts  # auth middleware for protected routes
│   ├── env.ts             # Zod-validated env vars (never use process.env directly)
│   └── utils.ts           # Pure utility functions (cn() for className merging, etc.)
├── server/
│   ├── actions/           # Server actions — one file per domain
│   │   ├── auth.ts
│   │   ├── projects.ts
│   │   └── billing.ts
│   ├── queries/           # Read queries — reusable across pages/actions
│   │   └── projects.ts
│   └── mutations/         # Write operations — transactional, validated
│       └── projects.ts
├── types/
│   └── index.ts           # Shared types, Zod inference types
└── middleware.ts           # Next.js middleware (auth redirects, i18n, rate limiting)
```

**At project root:**
```
drizzle/
├── migrations/            # Drizzle-generated SQL migration files
├── migrate.ts            # Migration runner script
└── seed.ts               # Seed script for local development
.env.example              # Documented env template (no secrets)
drizzle.config.ts         # Drizzle Kit configuration
tailwind.config.ts        # Tailwind configuration
components.json           # shadcn/ui configuration
```

### Why This Structure

- **`src/` directory**: Keeps config at root, code inside. Cleaner `tsconfig` paths.
- **Route groups `(marketing)`/`(dashboard)`**: Separate layouts without URL segments. The dashboard layout handles auth — no repetitive auth checks.
- **`server/` directory**: All server-only code in one place. `server/actions/` are React Server Actions (form handlers). `server/queries/` are reusable read functions. `server/mutations/` are transactional writes. The split forces separation of reads and writes (CQRS-lite).
- **`components/[feature]/`**: Feature-colocated, not type-colocated. Finding all billing-related components is one directory, not scattered across `components/cards/`, `components/forms/`, etc.
- **API routes only for webhooks**: Mutations go through server actions (progressive enhancement, no JS needed for forms). API routes are for external callbacks (Stripe, webhooks) that can't call server actions.
- **No `src/app/actions/`**: Server actions belong in `server/actions/` so they're importable by both pages and external systems (jobs, CLI, tests).

---

## SQL / Migration Conventions

### Database Client

```ts
// src/lib/db/index.ts — always use this import
import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import { env } from "@/lib/env";

const client = createClient({
  url: env.DATABASE_URL,
  authToken: env.DATABASE_AUTH_TOKEN, // Turso token, undefined for local
});

export const db = drizzle(client, { schema });
```

**Singleton pattern**: One import, one client. Never create a second client instance.

### Schema Rules

```ts
// src/lib/db/schema.ts
import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";

export const projects = sqliteTable("projects", {
  id: text("id").primaryKey(),           // CUID2 — not auto-increment
  userId: text("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$onUpdateFn(() => new Date()),
});
```

**Rules:**

1. **Use CUID2 for primary keys** (`text`), not auto-increment integers. Reason: CUID2s are globally unique, sortable, URL-safe, and safe to generate client-side (optimistic inserts). No ID collision when merging databases.

2. **Always add `createdAt`/`updatedAt`**. Every table. Non-negotiable. Use Drizzle's `$defaultFn` and `$onUpdateFn` — never manually set these.

3. **Foreign keys with `onDelete`**. Cascade or restrict, never leave default (which is no action in SQLite). Be explicit about data integrity.

4. **Snake_case in database, camelCase in TypeScript**. Drizzle maps automatically. This is standard SQL convention.

5. **Timestamps as integers with `{ mode: "timestamp" }`**. Drizzle handles conversion to JS `Date`. Efficient storage, no timezone ambiguity.

6. **One file per schema, not per table**. `schema.ts` holds all tables. SQLite doesn't have schemas; splitting is cosmetic and hurts discoverability.

7. **Nullable with intent**. Every nullable column gets a comment explaining why. `text("deleted_at")` is nullable because soft-delete. `text("avatar_url")` is nullable because optional. No silent nullables.

### Migration Rules

```bash
# Generate migration from schema changes
pnpm db:generate   # drizzle-kit generate — creates SQL in drizzle/migrations/

# Apply migrations (local: direct, prod: via Turso CLI)
pnpm db:migrate    # drizzle-kit migrate

# Seed local dev data
pnpm db:seed       # tsx drizzle/seed.ts
```

**Rules:**

1. **Migrations are the source of truth** for schema changes. Never modify the database directly. Even in development.

2. **One migration per logical change**. Adding a `projects` table and its `tasks` table? One migration file. Adding a column to an existing table weeks later? Separate migration.

3. **Migrations are plain SQL, reviewed in PRs**. Drizzle generates the SQL; you review it. No ORM magic you can't audit.

4. **No data migrations in Drizzle Kit migrations**. Data backfills go in separate scripts (`drizzle/backfill-*.ts`) run manually. Schema migrations change structure; data migrations change content. Separating them prevents accidental data corruption from a failed schema change.

5. **Never `DROP COLUMN` in SQLite without a migration plan**. SQLite doesn't support `DROP COLUMN` in older versions. Use Drizzle's built-in workaround or add a `deprecated_` prefix and drop later.

6. **Local dev uses better-sqlite3, production uses Turso**. The Drizzle config points to different drivers. Test migrations locally before pushing to Turso.

---

## Component Patterns

### Server Components by Default

```tsx
// Always start as a server component. Only add "use client" when necessary.
export default async function ProjectPage({
  params,
}: {
  params: { projectId: string };
}) {
  const project = await getProject(params.projectId);
  return <ProjectDetail project={project} />;
}
```

**Rule**: Every new component starts as a Server Component. Add `"use client"` only when you need: `useState`, `useEffect`, event handlers (`onClick`), browser APIs, or context consumers. Reason: Server Components ship zero JS, load faster, and can directly access the database.

### Co-located Data Fetching

```tsx
// The page (or parent server component) fetches data, passes to children as props.
// Children are pure render functions — no data fetching inside them.

// ✅ CORRECT — data flows down
export default async function ProjectPage({ params }: { params: { projectId: string } }) {
  const project = await getProject(params.projectId);       // server query
  const tasks = await getTasksForProject(params.projectId); // server query (parallel)
  return (
    <div>
      <ProjectHeader project={project} />
      <TaskList tasks={tasks} />
    </div>
  );
}

// ❌ WRONG — child fetches its own data
function TaskList({ projectId }: { projectId: string }) {
  const tasks = await getTasksForProject(projectId); // hidden data dependency
  return <ul>{tasks.map(...)}</ul>;
}
```

**Why**: Co-locating data fetching at the page level makes dependencies explicit and enables parallel fetching (React streams both queries concurrently). Children that fetch their own data create invisible waterfalls.

### Client Boundaries

```tsx
// Client components are leaf nodes — at the edges of your tree.
// They receive data as props from server parents.

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface ProjectActionsProps {
  projectId: string;
  initialStarred: boolean;
}

export function ProjectActions({ projectId, initialStarred }: ProjectActionsProps) {
  const [starred, setStarred] = useState(initialStarred);

  return (
    <Button
      variant={starred ? "default" : "outline"}
      onClick={async () => {
        await toggleStar(projectId);
        setStarred(!starred);
      }}
    >
      {starred ? "Starred" : "Star"}
    </Button>
  );
}
```

**Rule**: Use the "server parent → client child" pattern. Pass initial state from the server. The client component handles interactivity. No client-side data fetching unless it's real-time (polling, websockets).

### Form Pattern (Server Actions)

```tsx
// src/components/projects/CreateProjectForm.tsx
"use client";

import { useActionState } from "react";
import { createProject } from "@/server/actions/projects";

export function CreateProjectForm() {
  const [state, formAction, isPending] = useActionState(createProject, null);

  return (
    <form action={formAction}>
      <input name="name" required placeholder="Project name" />
      {state?.error && <p className="text-destructive">{state.error}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Creating..." : "Create"}
      </button>
    </form>
  );
}
```

```ts
// src/server/actions/projects.ts
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";
import { auth } from "@/lib/auth";
import { createProject as insertProject } from "@/server/mutations/projects";

const schema = z.object({
  name: z.string().min(1).max(100),
});

export async function createProject(_prev: unknown, formData: FormData) {
  const session = await auth();
  if (!session?.user?.id) return { error: "Unauthorized" };

  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten().fieldErrors };

  await insertProject({ ...parsed.data, userId: session.user.id });
  revalidatePath("/dashboard");
  return { success: true };
}
```

**Rules:**
- Every server action validates with Zod. Never trust client input.
- `revalidatePath` after mutations. No optimistic cache — revalidate is fast enough for SQLite.
- Actions return `{ error }` or `{ success }`. Client reads `state.error`.
- `useActionState` over `useTransition` + manual `useState`. Handles pending state, errors, and reset in one hook.

---

## What We Don't Do (And Why)

### ❌ No Prisma
Prisma adds a heavy codegen step, a binary engine, and an abstraction layer that fights SQLite's simplicity. Drizzle is SQL-first, lighter, and generates migrations you can read and audit. For a SQLite project, Drizzle is the right abstraction level.

### ❌ No monorepo / Turborepo
Premature for a single Next.js app. A monorepo adds tooling complexity, CI slowness, and dependency management overhead that doesn't pay off until you have 3+ deployable units. Start simple, split later.

### ❌ No tRPC
App Router with server actions and server components already provides end-to-end type safety between server and client without an RPC layer. tRPC adds a dependency and ceremony for a problem Next.js has already solved natively.

### ❌ No `pages/` directory
This is an App Router project. No hybrid migration. The `pages/` directory creates mental overhead about where to put things and breaks the unified mental model.

### ❌ No ORM-level relations for queries
Drizzle Relations API is useful for schema definitions, but not for queries. Write explicit SQL joins or use Drizzle's query builder. ORM-level relation loading (`with: { tasks: true }`) makes it too easy to N+1 and hides query complexity.

### ❌ No client-side data fetching libraries (React Query, SWR)
Server components fetch data on the server. For client-side mutations, server actions + `revalidatePath` are sufficient. React Query adds state management complexity for a problem the App Router already solves. The exception: real-time data (polling, subscriptions). Cross that bridge when you reach it.

### ❌ No barrel exports (`index.ts` re-exporting from other files)
Barrel files confuse bundlers (they can't tree-shake easily), slow down build times, and make stack traces harder to read. Import directly from the file you need: `import { Button } from "@/components/ui/button"` not `from "@/components/ui"`.

### ❌ No `any` or `as` type assertions
If you need to cast, the types are wrong. Fix the types, don't suppress the error. The only allowed `as` is for Zod inference: `type Project = z.infer<typeof projectSchema>`.

---

## Dev Commands

```bash
# Install dependencies
pnpm install

# Start development server (Turbopack)
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint and format
pnpm lint         # ESLint
pnpm format       # Prettier (or use Biome)

# Type checking
pnpm typecheck    # tsc --noEmit

# Database
pnpm db:generate  # Generate migration files from schema.ts changes
pnpm db:migrate   # Apply migrations to local or Turso database
pnpm db:seed      # Seed local database with sample data
pnpm db:studio    # Launch Drizzle Studio (local GUI) on port 4983

# Auth
pnpm auth:generate # Generate Better Auth secret

# Testing
pnpm test         # Vitest — unit + integration tests
pnpm test:e2e     # Playwright — end-to-end tests

# Components
pnpm ui:add       # Add a shadcn/ui component (e.g., pnpm ui:add button)
```

---

## Patterns to Follow

### Pattern 1: Environment Validation at Startup

```ts
// src/lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  DATABASE_AUTH_TOKEN: z.string().optional(), // not needed for local better-sqlite3
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

**Why**: Fail fast at import time, not 20 minutes into a debugging session. Every env var is validated and typed. No more `process.env.SECRET!` assertions.

### Pattern 2: Auth Middleware (Not Per-Page Guards)

```ts
// src/middleware.ts
import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isAuthed = !!req.auth?.user;
  const isDashboard = req.nextUrl.pathname.startsWith("/dashboard");

  if (isDashboard && !isAuthed) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/dashboard/:path*"], // only run on protected routes
};
```

**Why**: Middleware runs at the edge before rendering. One place for auth logic, not scattered across layouts and pages. The `matcher` config ensures auth checks only run where needed.

### Pattern 3: Optimistic UI with Server Validation

When showing immediate feedback, update the UI optimistically but always validate server-side. The server action is the authority. Client state is a cache.

### Pattern 4: Single-Purpose Server Actions

One action = one mutation. `createProject`, not `mutateProject(type, data)`. Named actions are easier to audit, test, and debug. The action name is the intent.

### Pattern 5: Streaming with Suspense

```tsx
// Heavy component? Wrap in Suspense with a skeleton fallback.
import { Suspense } from "react";

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<ProjectsSkeleton />}>
        <ProjectList /> {/* streams when ready */}
      </Suspense>
    </div>
  );
}
```

**Why**: Next.js App Router streams server components. Wrapping slow queries in Suspense gives users a skeleton instantly rather than a blank screen. The page is interactive before all data loads.

### Pattern 6: CUID2 ID Generation

```ts
// IDs are generated at the application layer, not in the database.
import { createId } from "@paralleldrive/cuid2";

const id = createId(); // "tz4a98xxat96iws9zmbrgj3a"
```

**Why**: Client-side ID generation enables optimistic inserts. No round-trip to the database for an ID. CUID2s are URL-safe, sortable by creation time, and collision-resistant even across distributed systems.

---

## Anti-Patterns

### Anti-Pattern 1: `useEffect` for Data Fetching

```tsx
// ❌ 99% of the time, this is wrong in Next.js App Router
useEffect(() => {
  fetch("/api/projects").then(setProjects);
}, []);
```

**Fix**: Fetch in a server component and pass data as props. If you need client-side fetching, use a server action with `useActionState` or a dedicated API route for real-time polling.

### Anti-Pattern 2: API Routes for Mutations in App Router

```tsx
// ❌ Creating a project via fetch() in a client component
fetch("/api/projects", { method: "POST", body: JSON.stringify(data) });
```

**Fix**: Use server actions. They work without JavaScript (progressive enhancement), provide type safety out of the box, and handle serialization automatically.

### Anti-Pattern 3: `"use client"` on the Page Root

```tsx
// ❌ Making the entire page a client component
"use client";
export default function DashboardPage() { ... }
```

**Fix**: Push `"use client"` down to the leaf components that need interactivity. The page shell stays as a server component. This maximizes server-rendered content.

### Anti-Pattern 4: Direct Database Access in Client Components

```tsx
// ❌ Importing db client in a client component
"use client";
import { db } from "@/lib/db"; // This won't work — and shouldn't.
```

**Fix**: Database queries go in server components, server actions, or API routes. Never expose the database to the client bundle.

### Anti-Pattern 5: Deeply Nested Data Fetching

```tsx
// ❌ Each component fetches its own data — invisible waterfall
export default function Page() {
  return <ProjectsList />; // fetches inside
}
function ProjectsList() {
  return projects.map(p => <ProjectCard id={p.id} />);
}
function ProjectCard({ id }) {
  const project = await getProject(id); // nested fetch
  const tasks = await getTasks(id);     // serial after project
  return ...;
}
```

**Fix**: Fetch at the top, pass data down. Use `Promise.all` for parallel fetches at the page level. Same data, 3x faster.

### Anti-Pattern 6: Using `as` to Paper Over Type Gaps

```tsx
// ❌ Suppressing type errors instead of fixing them
const data = await db.select().from(projects) as unknown as ProjectWithTasks[];
```

**Fix**: Define the type correctly. Use Zod inference or Drizzle's `$inferSelect`. If the query returns something unexpected, the type should reflect that.

### Anti-Pattern 7: Inline SQL in Server Components

```tsx
// ❌ Raw SQL strings in components
const projects = await db.all("SELECT * FROM projects WHERE user_id = ?", [userId]);
```

**Fix**: Use Drizzle's query builder. Raw SQL belongs in migration files or dedicated query functions in `server/queries/`, never inline in components.

---

## Testing

- **Unit tests**: `src/lib/` and `src/server/mutations/` — pure logic, easy to test.
- **Integration tests**: `src/server/actions/` — test the full flow (validation → mutation → revalidation) with a test SQLite database.
- **E2E tests**: Playwright against the dev server. Test critical user flows (sign up → create project → invite member).
- **No snapshot tests**: They break on any intentional change and create noise. Test behavior, not rendering output strings.

---

## File Naming

- **Components**: `PascalCase.tsx` — `ProjectCard.tsx`, `CreateProjectForm.tsx`
- **Server actions/queries**: `kebab-case.ts` — `projects.ts`, `auth.ts` (they're modules, not components)
- **Utility files**: `kebab-case.ts` — `cn.ts`, `env.ts`
- **Route params**: `[paramName]` for dynamic, `[...catchAll]` for catch-all
- **Private files**: Prefix with `_` — `_components/`, `_utils.ts`. Next.js won't route them.

---

## Ports & URLs

- Dev server: `http://localhost:3000`
- Drizzle Studio: `http://localhost:4983`
- Better Auth default callback: `/api/auth/callback`
- Production: Deployed to Vercel (or any Node.js host)

---

> **Last updated**: 2026-05-16
> **Maintainer note**: When adding new conventions, always include the *why*.
> A rule without a reason gets ignored. A rule with a reason gets followed.
