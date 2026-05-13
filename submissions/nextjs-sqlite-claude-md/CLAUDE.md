# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the single source of truth for how this codebase works. Read it fully before writing any code.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | **Next.js 15 (App Router)** | Server Components by default eliminate client-side data fetching boilerplate. App Router is the stable future of Next.js — Pages Router is legacy. |
| UI Library | **React 19** | Required by Next.js 15. `use()` hook and Server Components are first-class. |
| Language | **TypeScript 5 (strict mode)** | `strict: true` in tsconfig catches null errors at compile time, not in production. No `any` — ever. |
| Database | **better-sqlite3** (dev/single-server) / **Turso** (prod/edge) | SQLite is the simplest correct database for SaaS under 10M rows. better-sqlite3 is synchronous, which means no connection pool bugs. Turso adds replication when you outgrow a single server. |
| ORM | **Drizzle ORM** | Type-safe SQL with zero runtime overhead. Unlike Prisma, it produces readable SQL and doesn't require a binary engine. |
| Styling | **Tailwind CSS 4** | Utility-first CSS eliminates naming debates and dead CSS. v4 uses CSS-native `@theme` — no more `tailwind.config.js`. |
| Auth | **Lucia Auth v3** (or Auth.js v5) | Lucia gives full control over session storage in SQLite. No external auth service dependency. |
| Validation | **Zod** | Runtime validation at API boundaries. Shares types with TypeScript — define once, validate everywhere. |
| Package Manager | **pnpm** | Strict dependency resolution prevents phantom dependencies. Faster and more disk-efficient than npm. |

### Node Version

```
node >= 20.0.0
pnpm >= 9.0.0
```

Use `.nvmrc` with `20` pinned. No `engines` field games — just pin it.

---

## Project Structure

```
.
├── CLAUDE.md                          # You are here
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── (auth)/                    # Route group: login, signup, forgot-password
│   │   │   ├── login/page.tsx
│   │   │   ├── signup/page.tsx
│   │   │   └── layout.tsx             # Shared auth layout (centered card)
│   │   ├── (dashboard)/               # Route group: authenticated pages
│   │   │   ├── layout.tsx             # Sidebar + auth guard
│   │   │   ├── page.tsx               # Dashboard home
│   │   │   ├── settings/
│   │   │   │   └── page.tsx
│   │   │   └── [teamSlug]/
│   │   │       ├── page.tsx
│   │   │       └── projects/
│   │   │           ├── page.tsx
│   │   │           └── [projectId]/
│   │   │               └── page.tsx
│   │   ├── api/                       # Route Handlers (REST-style)
│   │   │   ├── auth/
│   │   │   │   └── [...nextauth]/route.ts
│   │   │   └── webhooks/
│   │   │       └── stripe/route.ts
│   │   ├── layout.tsx                 # Root layout (html, body, providers)
│   │   ├── not-found.tsx
│   │   └── error.tsx
│   ├── components/
│   │   ├── ui/                        # Primitive UI components (Button, Input, Card)
│   │   ├── forms/                     # Form components with validation wired in
│   │   ├── layouts/                   # Sidebar, Header, Footer
│   │   └── features/                  # Feature-specific composed components
│   │       ├── projects/
│   │       │   ├── project-list.tsx
│   │       │   └── project-card.tsx
│   │       └── billing/
│   │           └── plan-selector.tsx
│   ├── lib/
│   │   ├── db/
│   │   │   ├── index.ts               # Database connection (better-sqlite3 / Turso client)
│   │   │   ├── schema.ts              # Drizzle schema (all tables)
│   │   │   ├── migrations/            # SQL migration files
│   │   │   │   ├── 0001_create_users.sql
│   │   │   │   └── 0002_create_teams.sql
│   │   │   └── seed.ts                # Dev seed data
│   │   ├── auth/
│   │   │   ├── index.ts               # Auth config and helpers
│   │   │   └── middleware.ts          # Auth middleware logic
│   │   ├── validations/               # Zod schemas, organized by domain
│   │   │   ├── auth.ts
│   │   │   ├── project.ts
│   │   │   └── team.ts
│   │   └── utils.ts                   # Pure utility functions (< 20 lines each)
│   ├── actions/                       # Server Actions, organized by domain
│   │   ├── auth.ts
│   │   ├── project.ts
│   │   └── team.ts
│   ├── queries/                       # Read-only database queries (Server Components use these)
│   │   ├── project.ts
│   │   ├── team.ts
│   │   └── user.ts
│   └── types/
│       └── index.ts                   # Shared TypeScript types (not Drizzle-generated ones)
├── public/
├── drizzle.config.ts
├── next.config.ts
├── tailwind.css                       # Tailwind v4 entry point (replaces tailwind.config.js)
├── tsconfig.json
├── .env.local                         # Local secrets — NEVER commit
├── .env.example                       # Template with dummy values — ALWAYS commit
└── package.json
```

### Why This Structure

- **`actions/` separate from `app/`** — Server Actions are reusable across routes. Co-locating them with pages creates duplication when two pages need the same mutation.
- **`queries/` separate from `actions/`** — Reads and writes have different concerns. Queries are called from Server Components directly. Actions handle form submissions and mutations. Mixing them makes it unclear what has side effects.
- **`components/ui/` vs `components/features/`** — UI components know nothing about business logic. Feature components compose UI components with domain data. This separation makes UI components reusable across features.
- **Route groups `(auth)` and `(dashboard)`** — Parenthesized folders create layout boundaries without affecting URLs. Auth pages get a centered layout. Dashboard pages get a sidebar. Neither affects the URL path.
- **`lib/validations/`** — Zod schemas live here, not next to components, because both Server Actions and API routes validate the same shapes. Single source of truth for validation.

---

## Dev Commands

```bash
# Install dependencies
pnpm install

# Start dev server (port 3000)
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Type checking (no emit)
pnpm typecheck        # tsc --noEmit

# Lint
pnpm lint             # next lint + eslint

# Format
pnpm format           # prettier --write .
pnpm format:check     # prettier --check . (CI)

# Database
pnpm db:generate      # drizzle-kit generate (create migration from schema changes)
pnpm db:migrate       # drizzle-kit migrate (apply pending migrations)
pnpm db:push          # drizzle-kit push (apply schema directly — dev only, skips migration files)
pnpm db:studio        # drizzle-kit studio (visual database browser)
pnpm db:seed          # tsx src/lib/db/seed.ts

# Testing
pnpm test             # vitest run
pnpm test:watch       # vitest (watch mode)
pnpm test:e2e         # playwright test
```

### package.json scripts block

```jsonc
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:push": "drizzle-kit push",
    "db:studio": "drizzle-kit studio",
    "db:seed": "tsx src/lib/db/seed.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test"
  }
}
```

---

## Naming Conventions

### Files & Directories

| Type | Convention | Example | Why |
|------|-----------|---------|-----|
| React components | `kebab-case.tsx` | `project-card.tsx` | Filesystem-safe on all OSes. Next.js convention. Avoids case-sensitivity bugs between macOS (insensitive) and Linux (sensitive). |
| Server Actions | `kebab-case.ts` in `actions/` | `actions/project.ts` | Grouped by domain, not by action name. One file per domain keeps related mutations together. |
| Queries | `kebab-case.ts` in `queries/` | `queries/project.ts` | Mirrors actions structure. Easy to find "where does project data come from?" |
| Utilities | `kebab-case.ts` | `utils.ts` | No barrel files except `types/index.ts`. Barrel files break tree-shaking and make imports opaque. |
| Database migrations | `NNNN_snake_description.sql` | `0001_create_users.sql` | Sequential numbering ensures ordering. Snake case matches SQL conventions. |
| Route files | `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` | (Next.js convention) | These are framework-reserved names. Don't fight the framework. |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL` | Universal convention. Prefix with `NEXT_PUBLIC_` only for client-exposed values. |

### React Components

```tsx
// File: src/components/features/projects/project-card.tsx

// Named export — NEVER default export components.
// Why: Default exports allow inconsistent naming across imports.
// Named exports enforce a single canonical name.
export function ProjectCard({ project }: ProjectCardProps) {
  return <div>...</div>;
}

// Props type is always ComponentNameProps, defined in the same file.
// Why: Co-location. You never need to hunt for the type.
type ProjectCardProps = {
  project: Project;
};
```

**Default exports are reserved for Next.js file conventions only** (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`). Everything else uses named exports because default exports allow different import names for the same component, which makes codebase-wide refactoring unreliable.

### Database Tables & Columns

| Convention | Example | Why |
|-----------|---------|-----|
| Table names: **plural snake_case** | `users`, `team_members`, `project_invites` | SQL convention. Plural because a table contains many rows. |
| Column names: **snake_case** | `created_at`, `team_id`, `is_active` | SQL convention. Drizzle maps these to camelCase in TypeScript automatically. |
| Primary keys: **`id`** (always) | `id TEXT PRIMARY KEY` | Consistency. Never `user_id` as a PK — that's for foreign keys. |
| Foreign keys: **`{singular_table}_id`** | `user_id`, `team_id` | Makes JOIN conditions self-documenting: `users.id = projects.user_id`. |
| Booleans: **`is_` or `has_` prefix** | `is_active`, `has_accepted_invite` | Reads naturally: `WHERE is_active = 1`. |
| Timestamps: **`_at` suffix** | `created_at`, `updated_at`, `deleted_at` | Distinguishes timestamps from booleans or plain dates. |
| IDs: **CUID2 strings** | `clx1abc23def456` | URL-safe, collision-resistant, no sequential leaking. Use `@paralleldrive/cuid2`. Never auto-increment integers — they leak row counts and are guessable. |

### API Routes

| Convention | Example | Why |
|-----------|---------|-----|
| RESTful plurals | `/api/projects`, `/api/projects/[id]` | Predictable. `/api/project` (singular) is a common mistake that creates inconsistency. |
| Kebab-case paths | `/api/team-members` | URL convention. Never camelCase in URLs. |
| Prefer Server Actions over API routes | Use API routes only for webhooks, OAuth callbacks, and third-party integrations | Server Actions provide type safety, automatic revalidation, and progressive enhancement. API routes require manual fetch, error handling, and type casting. |

---

## SQL / Migration Conventions

### Writing Migrations

Every schema change goes through a migration. Never modify the production database by hand.

```bash
# Workflow:
# 1. Edit src/lib/db/schema.ts
# 2. Generate migration
pnpm db:generate
# 3. Review the generated SQL in src/lib/db/migrations/
# 4. Apply
pnpm db:migrate
```

### Drizzle Schema Example

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

// Every table gets these four columns. No exceptions.
// Why: created_at and updated_at are needed for debugging and auditing.
// deleted_at enables soft deletes — you can always recover data.

export const users = sqliteTable("users", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  passwordHash: text("password_hash").notNull(),
  isActive: integer("is_active", { mode: "boolean" }).notNull().default(true),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
});

export const teams = sqliteTable("teams", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => createId()),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  ownerId: text("owner_id")
    .notNull()
    .references(() => users.id),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
});

export const teamMembers = sqliteTable("team_members", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => createId()),
  teamId: text("team_id")
    .notNull()
    .references(() => teams.id),
  userId: text("user_id")
    .notNull()
    .references(() => users.id),
  role: text("role", { enum: ["owner", "admin", "member"] })
    .notNull()
    .default("member"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});
```

### Migration File Conventions

Generated migration files are in `src/lib/db/migrations/`. Rules:

1. **Never edit a migration that has been applied to any environment** — create a new one instead. Editing applied migrations causes drift between environments.
2. **One concern per migration** — `0003_add_billing_columns.sql` not `0003_add_billing_and_fix_users_and_create_invoices.sql`. Atomic migrations are easier to debug when one fails.
3. **Always include `DOWN` logic as a comment** — SQLite doesn't support `ALTER TABLE DROP COLUMN` before 3.35.0, so document how to reverse the migration even if it requires a table rebuild.
4. **Timestamps in SQLite are stored as integers (Unix epoch)** — not ISO strings. Integer comparison is faster and avoids timezone bugs. Drizzle handles the conversion.
5. **Use `STRICT` tables when possible** — SQLite's type affinity is surprising. `STRICT` mode enforces types:

```sql
CREATE TABLE invoices (
  id TEXT PRIMARY KEY,
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'usd',
  created_at INTEGER NOT NULL
) STRICT;
```

### Database Connection

```typescript
// src/lib/db/index.ts
import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";
import * as schema from "./schema";

// WAL mode is critical for SQLite in a web server:
// - Allows concurrent reads during writes
// - Without it, writes block ALL reads
const sqlite = new Database(process.env.DATABASE_URL ?? "local.db");
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("busy_timeout = 5000");
sqlite.pragma("synchronous = NORMAL");
sqlite.pragma("cache_size = 1000000000");  // 1GB — SQLite's default is tiny
sqlite.pragma("foreign_keys = true");       // SQLite does NOT enforce FKs by default
sqlite.pragma("temp_store = memory");

export const db = drizzle(sqlite, { schema });
```

**Why each pragma matters:**
- `journal_mode = WAL` — Write-Ahead Logging allows readers and writers to operate concurrently. Default rollback journal blocks everything.
- `busy_timeout = 5000` — Wait 5 seconds for a lock instead of failing immediately. Prevents `SQLITE_BUSY` errors under load.
- `synchronous = NORMAL` — Balances durability and speed. `FULL` is overkill with WAL mode. `OFF` risks corruption.
- `foreign_keys = true` — SQLite ignores foreign key constraints by default. This is a footgun. Always enable.

---

## Component Patterns

### Server Components (Default)

Every component is a Server Component unless it needs interactivity. This is the most important rule in Next.js 15.

```tsx
// src/app/(dashboard)/[teamSlug]/projects/page.tsx
// This is a Server Component — no "use client" directive.
// It runs on the server, has zero JS bundle cost, and can access the database directly.

import { getTeamProjects } from "@/queries/project";
import { ProjectList } from "@/components/features/projects/project-list";

export default async function ProjectsPage({
  params,
}: {
  params: Promise<{ teamSlug: string }>;
}) {
  const { teamSlug } = await params;
  const projects = await getTeamProjects(teamSlug);

  return (
    <div>
      <h1>Projects</h1>
      {/* ProjectList is also a Server Component. It receives data as props.
          No useEffect. No loading states. No client-side fetch. */}
      <ProjectList projects={projects} />
    </div>
  );
}
```

### Client Components (Only When Required)

Add `"use client"` only for: event handlers, useState, useEffect, browser APIs, or third-party client-only libraries.

```tsx
// src/components/features/projects/create-project-dialog.tsx
"use client";

// Why client? This component uses useState for dialog open/close
// and calls a Server Action on form submit.

import { useState } from "react";
import { useActionState } from "react";
import { createProject } from "@/actions/project";
import { Button } from "@/components/ui/button";

export function CreateProjectDialog({ teamId }: { teamId: string }) {
  const [open, setOpen] = useState(false);
  const [state, action, pending] = useActionState(createProject, null);

  return (
    <>
      <Button onClick={() => setOpen(true)}>New Project</Button>
      {open && (
        <form action={action}>
          <input type="hidden" name="teamId" value={teamId} />
          <input name="name" required placeholder="Project name" />
          {state?.error && <p className="text-red-500">{state.error}</p>}
          <Button type="submit" disabled={pending}>
            {pending ? "Creating..." : "Create"}
          </Button>
        </form>
      )}
    </>
  );
}
```

### Server Actions

```typescript
// src/actions/project.ts
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { db } from "@/lib/db";
import { projects } from "@/lib/db/schema";
import { createProjectSchema } from "@/lib/validations/project";
import { getCurrentUser } from "@/lib/auth";

// Every Server Action follows this pattern:
// 1. Authenticate
// 2. Validate input with Zod
// 3. Authorize (does this user have permission?)
// 4. Mutate database
// 5. Revalidate cache
// 6. Return result or redirect

export async function createProject(_prevState: unknown, formData: FormData) {
  // 1. Authenticate — ALWAYS first. Never trust the client.
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  // 2. Validate — parse, don't validate. Zod gives us a typed result.
  const parsed = createProjectSchema.safeParse({
    name: formData.get("name"),
    teamId: formData.get("teamId"),
  });

  if (!parsed.success) {
    return { error: parsed.error.errors[0].message };
  }

  // 3. Authorize — verify the user is a member of this team
  const membership = await db.query.teamMembers.findFirst({
    where: (tm, { and, eq }) =>
      and(eq(tm.teamId, parsed.data.teamId), eq(tm.userId, user.id)),
  });

  if (!membership) {
    return { error: "You are not a member of this team." };
  }

  // 4. Mutate
  const [project] = await db
    .insert(projects)
    .values({
      name: parsed.data.name,
      teamId: parsed.data.teamId,
      createdById: user.id,
    })
    .returning();

  // 5. Revalidate — tell Next.js this data changed
  revalidatePath(`/${parsed.data.teamId}/projects`);

  // 6. Redirect to the new project
  redirect(`/${parsed.data.teamId}/projects/${project.id}`);
}
```

### Queries (Read-Only Data Access)

```typescript
// src/queries/project.ts
import { db } from "@/lib/db";
import { projects, teams } from "@/lib/db/schema";
import { eq, and, isNull } from "drizzle-orm";
import { cache } from "react";

// Wrap queries with React's cache() to deduplicate within a single request.
// Why: If a layout and a page both call getTeamProjects(), the database
// is only hit once. React deduplicates by reference equality.

export const getTeamProjects = cache(async (teamSlug: string) => {
  return db
    .select()
    .from(projects)
    .innerJoin(teams, eq(teams.id, projects.teamId))
    .where(and(eq(teams.slug, teamSlug), isNull(projects.deletedAt)));
});

export const getProjectById = cache(async (projectId: string) => {
  return db.query.projects.findFirst({
    where: (p, { eq }) => eq(p.id, projectId),
  });
});
```

### Data Fetching Hierarchy

This is the order of preference for data access. Use the first option that works:

1. **Server Component + query function** — Direct database access. Zero client JS. Best for initial page loads.
2. **Server Action** — For mutations triggered by forms or buttons. Handles revalidation automatically.
3. **Route Handler (`route.ts`)** — Only for webhooks, OAuth callbacks, file downloads, and third-party API integrations that can't use Server Actions.
4. **Client-side fetch (SWR/React Query)** — Last resort. Only for real-time data that must poll or use WebSockets (e.g., live dashboard, chat).

### Loading & Error States

```tsx
// src/app/(dashboard)/[teamSlug]/projects/loading.tsx
// Next.js automatically wraps page.tsx with this Suspense boundary.
// No manual <Suspense> needed at the page level.

export default function Loading() {
  return <ProjectListSkeleton />;
}
```

```tsx
// src/app/(dashboard)/[teamSlug]/projects/error.tsx
"use client"; // Error boundaries MUST be client components

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

---

## Anti-Patterns

These are specific mistakes. Each one has been made, caused a bug, and earned its place here.

### 1. DO NOT use `useEffect` for data fetching

```tsx
// BAD — Client-side fetch in useEffect
"use client";
export function ProjectList() {
  const [projects, setProjects] = useState([]);
  useEffect(() => {
    fetch("/api/projects").then(r => r.json()).then(setProjects);
  }, []);
  return <div>{projects.map(...)}</div>;
}
```

```tsx
// GOOD — Server Component with direct query
export async function ProjectList({ teamSlug }: { teamSlug: string }) {
  const projects = await getTeamProjects(teamSlug);
  return <div>{projects.map(...)}</div>;
}
```

**Why:** The `useEffect` version causes a loading waterfall (page loads, JS executes, fetch fires, data renders). The Server Component version sends the HTML with data already embedded. Faster. No loading spinner. No layout shift. No race conditions on unmount.

### 2. DO NOT create API routes for data that Server Components can access

```
BAD:  app/api/projects/route.ts  →  fetched from a client component with useEffect
GOOD: queries/project.ts         →  called from a Server Component directly
```

**Why:** API routes for internal data access add an unnecessary network hop, require manual error handling, and lose type safety. They exist for external consumers, not for your own UI.

### 3. DO NOT put `"use client"` at the top of files "just to be safe"

**Why:** Every `"use client"` directive adds that component and all its imports to the client JS bundle. A 50-component page with `"use client"` on every file sends 50 components worth of JavaScript to the browser. Push `"use client"` to the smallest leaf components that actually need interactivity.

### 4. DO NOT use `parseInt(params.id)` for database IDs

```typescript
// BAD — Leaks row count, guessable, enumerable
const user = await db.query.users.findFirst({
  where: (u, { eq }) => eq(u.id, parseInt(params.id)),
});

// GOOD — CUID2 string IDs
const user = await db.query.users.findFirst({
  where: (u, { eq }) => eq(u.id, params.id),
});
```

**Why:** Auto-increment integer IDs leak your row count (competitor can hit `/users/1` through `/users/50000` and know your user base size). They're also enumerable, making scraping trivial. CUID2 strings are non-sequential, URL-safe, and globally unique.

### 5. DO NOT skip `foreign_keys = true` pragma

```typescript
// BAD — Default SQLite behavior
const sqlite = new Database("local.db");

// GOOD — Enforce referential integrity
const sqlite = new Database("local.db");
sqlite.pragma("foreign_keys = true");
```

**Why:** SQLite accepts `REFERENCES` clauses in `CREATE TABLE` but silently ignores them by default. Your foreign keys are decorative until you enable this pragma. You will insert orphaned rows. You will not notice until production.

### 6. DO NOT use `export default` for components

```tsx
// BAD — Allows inconsistent naming
export default function ProjectCard() { ... }
// File A: import Card from './project-card'
// File B: import ProjectCard from './project-card'
// File C: import Foo from './project-card'

// GOOD — Single canonical name
export function ProjectCard() { ... }
// Every file: import { ProjectCard } from './project-card'
```

**Why:** Default exports allow each importing file to use a different name. This makes rename-refactoring unreliable (find-and-replace misses aliases) and makes grep/search for component usage inaccurate.

### 7. DO NOT store timestamps as ISO strings in SQLite

```sql
-- BAD
created_at TEXT DEFAULT (datetime('now'))

-- GOOD
created_at INTEGER NOT NULL DEFAULT (unixepoch())
```

**Why:** String comparison for date ranges is slow and error-prone (timezone-dependent). Integer Unix timestamps are timezone-agnostic, sortable, indexable, and smaller in storage. Drizzle converts them to JavaScript `Date` objects automatically.

### 8. DO NOT use `try/catch` in Server Actions to swallow errors silently

```typescript
// BAD — Swallows the error. You'll never know it happened.
export async function deleteProject(id: string) {
  try {
    await db.delete(projects).where(eq(projects.id, id));
  } catch {
    // "it's fine"
  }
}

// GOOD — Return structured errors to the UI
export async function deleteProject(_prevState: unknown, formData: FormData) {
  try {
    await db.delete(projects).where(eq(projects.id, formData.get("id") as string));
    revalidatePath("/projects");
    return { success: true };
  } catch (error) {
    console.error("Failed to delete project:", error);
    return { error: "Failed to delete project. Please try again." };
  }
}
```

**Why:** Silent catches hide bugs. In Server Actions, return an error state that the UI can display. Log the actual error server-side for debugging.

### 9. DO NOT create barrel files (`index.ts` re-exports)

```
// BAD — src/components/ui/index.ts
export { Button } from './button';
export { Input } from './input';
export { Card } from './card';
// ... 50 more exports

// GOOD — Import directly
import { Button } from '@/components/ui/button';
```

**Why:** Barrel files defeat tree-shaking. Importing `{ Button }` from a barrel file that re-exports 50 components causes bundlers to evaluate all 50 modules. Direct imports are explicit, faster to resolve, and never cause circular dependency issues.

### 10. DO NOT validate on the client only

```tsx
// BAD — Client-only validation
"use client";
function CreateForm() {
  const handleSubmit = (e) => {
    if (!e.target.name.value) {
      setError("Name required");
      return;
    }
    // submit...
  };
}

// GOOD — Client validation for UX + Server validation for security
// Client: instant feedback
// Server Action: Zod validation (see Server Actions pattern above)
```

**Why:** Client-side validation is a UX convenience, not a security measure. Anyone can bypass it with curl. Always validate in the Server Action with Zod. Client validation is optional sugar on top.

---

## Environment Variables

```bash
# .env.example — commit this file

# Database
DATABASE_URL=local.db

# Auth
AUTH_SECRET=generate-with-openssl-rand-base64-32

# Turso (production only)
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token

# Stripe (if using billing)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**Rules:**
- `NEXT_PUBLIC_` prefix exposes the variable to client-side code. Only use for genuinely public values (Stripe publishable key, analytics IDs).
- Never put secrets in `NEXT_PUBLIC_` variables. They are embedded in the JS bundle and visible to anyone.
- Generate `AUTH_SECRET` with `openssl rand -base64 32`. Don't use a human-readable string.

---

## Testing Strategy

| Layer | Tool | What to Test |
|-------|------|-------------|
| Unit | Vitest | Utility functions, Zod schemas, pure logic |
| Integration | Vitest + better-sqlite3 in-memory | Database queries, Server Actions (with test DB) |
| E2E | Playwright | Critical user flows: signup, login, create project, billing |

### Test file naming

```
src/lib/utils.ts          → src/lib/utils.test.ts
src/actions/project.ts    → src/actions/project.test.ts
```

Tests live next to the code they test. Not in a separate `__tests__` directory. Why: when you move or delete a file, you see its test file and handle it too. Orphaned test files in a distant `__tests__` folder silently rot.

---

## Performance Rules

1. **Use `loading.tsx` for every route segment** — Free streaming SSR. The shell renders instantly while data loads.
2. **Use `React.cache()` to deduplicate queries** — A layout and page that both need the same data should not hit the database twice.
3. **Use `unstable_cache` or `next/cache` for expensive queries** — Time-bound caching for data that doesn't change on every request (e.g., plan pricing, feature flags).
4. **Images: always use `next/image`** — Automatic WebP/AVIF conversion, lazy loading, and responsive sizing. Never use raw `<img>` tags.
5. **Dynamic imports for heavy client components** — `next/dynamic` with `ssr: false` for components like rich text editors or chart libraries that are large and browser-only.
