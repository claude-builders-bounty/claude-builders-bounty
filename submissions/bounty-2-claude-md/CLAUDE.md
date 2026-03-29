# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells you everything about how this codebase is built and why. Read it
completely before making any change. Every rule has a reason. If a rule seems
wrong for your task, ask before breaking it.

---

## Why This File Exists

Without explicit conventions, AI assistants make subtly inconsistent choices:
sometimes using `useRouter`, sometimes `redirect()`, sometimes both. Sometimes
using `db.prepare()`, sometimes a helper function. The inconsistencies accumulate
and create codebases that feel "almost right" everywhere but correct nowhere.

This file eliminates that problem by making every convention explicit and giving
the **reason** behind each one. You can disagree with a reason — but then we
discuss it first, not after you've implemented it the wrong way.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | Server Components + Server Actions eliminate most API boilerplate |
| Language | TypeScript | 5.5+ | `strict: true`, no exceptions |
| Database (local dev) | better-sqlite3 | 11.x | Synchronous, zero-config, fast tests |
| Database (production) | Turso (libSQL) | latest | Edge-compatible SQLite, branching, replication |
| ORM/Query builder | Drizzle ORM | 0.30+ | TypeScript-first, zero runtime overhead, SQL-like syntax |
| Auth | Lucia v3 | 3.x | Session-based, SQLite-native, no magic |
| Validation | Zod | 3.x | Runtime + compile-time safety in one library |
| Styling | Tailwind CSS | 3.x | Utility classes = no CSS file sprawl |
| Testing | Vitest | 2.x | Fast, Jest-compatible, native ESM |
| E2E | Playwright | 1.x | Cross-browser, reliable selectors |
| Email | Resend | latest | Transactional email via API, no SMTP config |

**Do not add new dependencies without discussing.** Every added package is a
future security audit, a version conflict risk, and a maintenance burden.

---

## Environment Variables

All env vars are defined in `src/env.ts` using Zod. Access them **only** via
`env.*` — never `process.env.*` directly.

```typescript
// src/env.ts
import { z } from "zod";

const schema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  DATABASE_URL: z.string().url(),          // Turso: libsql://...
  DATABASE_AUTH_TOKEN: z.string().optional(), // Turso auth (not needed locally)
  LUCIA_SECRET: z.string().min(32),
  RESEND_API_KEY: z.string().startsWith("re_"),
  APP_URL: z.string().url(),
  NEXT_PUBLIC_APP_NAME: z.string(),
});

export const env = schema.parse(process.env);
export type Env = z.infer<typeof schema>;
```

**Why?** If an env var is missing, you get a clear error at startup, not a
confusing runtime failure two hours later in production.

**Do not** access `process.env.ANYTHING` outside `src/env.ts`. Not in Server
Actions. Not in route handlers. Not in Drizzle config. Import `env` instead.

---

## Folder Structure

```
src/
  app/                    Next.js App Router (pages + layouts + route handlers)
    (auth)/               Route group: unauthenticated pages (login, signup, etc.)
      login/
        page.tsx
      signup/
        page.tsx
    (dashboard)/          Route group: authenticated pages
      layout.tsx          Auth guard — redirects to /login if no session
      dashboard/
        page.tsx
    api/                  Route handlers (webhooks, external integrations only)
      webhooks/
        stripe/
          route.ts
  components/
    ui/                   Reusable, stateless UI primitives
      button.tsx
      input.tsx
      modal.tsx
    forms/                Form components with their own Server Action
      login-form.tsx
      create-project-form.tsx
  db/
    index.ts              Database client (Drizzle + Turso/better-sqlite3)
    schema.ts             All Drizzle table definitions in one file
    migrations/           Drizzle-generated migration SQL files
  lib/
    auth.ts               Lucia instance + session helpers
    errors.ts             AppError class
    utils.ts              Pure utility functions (no side effects)
  services/               Business logic (no HTTP, no UI)
    user.service.ts
    project.service.ts
  types/
    index.ts              Shared TypeScript types
  env.ts                  Zod-validated environment variables
  middleware.ts           Auth middleware (reads session cookie)
```

**Why route groups?** `(auth)` and `(dashboard)` group pages without affecting
the URL. The `(dashboard)/layout.tsx` handles auth for every page in that group
in one place.

**Why `services/`?** Server Actions should be thin. They validate input, call a
service function, and return a result. The service function contains all database
logic. This makes services testable without HTTP.

**Why keep `schema.ts` in one file?** Drizzle needs all tables visible at once
to generate correct migrations. Splitting it causes "Table X referenced before
definition" errors.

---

## Database

### Client Setup

```typescript
// src/db/index.ts
import { drizzle } from "drizzle-orm/libsql";
import { createClient } from "@libsql/client";
import * as schema from "./schema";
import { env } from "@/env";

// In test, use an in-memory database
const url =
  process.env.NODE_ENV === "test" ? ":memory:" : env.DATABASE_URL;

const client = createClient({
  url,
  authToken:
    process.env.NODE_ENV === "test" ? undefined : env.DATABASE_AUTH_TOKEN,
});

export const db = drizzle(client, { schema });
export type DB = typeof db;
```

**Why libSQL for tests?** better-sqlite3 is synchronous; libSQL is async but
uses `:memory:` for tests without a network call. Consistent API across
environments.

### Schema Conventions

```typescript
// src/db/schema.ts
import { text, integer, sqliteTable } from "drizzle-orm/sqlite-core";
import { relations } from "drizzle-orm";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),               // cuid2 string, NOT auto-increment
  email: text("email").notNull().unique(),
  hashedPassword: text("hashed_password"),   // null for OAuth users
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});

export const sessions = sqliteTable("sessions", {
  id: text("id").primaryKey(),
  userId: text("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  expiresAt: integer("expires_at").notNull(),
});

export const usersRelations = relations(users, ({ many }) => ({
  sessions: many(sessions),
}));
```

**Rules:**
- Use `cuid2` strings as primary keys, never `INTEGER PRIMARY KEY AUTOINCREMENT`.
  **Why?** Integer IDs are guessable (sequential). CUID2 is URL-safe, sortable,
  and works across distributed databases.
- All columns are `notNull()` unless there is an explicit reason for null.
  **Why?** Null adds a third possible value to every field. It forces null checks
  everywhere. Default to empty string or 0 if meaningful.
- Store timestamps as `integer` with `{ mode: "timestamp" }`.
  **Why?** SQLite has no native timestamp type. Integers are faster than text,
  and Drizzle's `timestamp` mode handles JS Date conversion.
- Column names are `snake_case` in the database, `camelCase` in TypeScript.
  Drizzle handles the mapping.

### Migrations

```bash
# Generate a migration after changing schema.ts
pnpm db:generate

# Apply migrations to local Turso dev database
pnpm db:migrate

# Never in production:
# pnpm db:push       -- pushes schema directly, no migration file, loses history
```

**Do not** use `db:push` for anything other than fast local prototyping during
initial development. Once a table has data, always generate a migration.

**Why?** `db:push` is destructive if your schema has breaking changes. Production
deployments must run the migration file, not guess at the diff.

Migration naming: `drizzle-kit generate` creates timestamped files. Do not rename
them. Do not edit them after they have been applied.

### Query Patterns

```typescript
// services/project.service.ts

import { db } from "@/db";
import { projects } from "@/db/schema";
import { eq, and, desc } from "drizzle-orm";
import { AppError } from "@/lib/errors";
import { createId } from "@paralleldrive/cuid2";

// READ: always use drizzle query builder, never raw SQL for standard queries
export async function getProjectsByUser(userId: string) {
  return db
    .select()
    .from(projects)
    .where(eq(projects.userId, userId))
    .orderBy(desc(projects.createdAt));
}

// CREATE: generate ID here, not in the DB
export async function createProject(
  userId: string,
  name: string
): Promise<typeof projects.$inferSelect> {
  const id = createId();
  const [project] = await db
    .insert(projects)
    .values({ id, userId, name })
    .returning();

  if (!project) throw new AppError("Failed to create project", 500);
  return project;
}

// UPDATE: always include userId in WHERE — never trust the client's projectId alone
export async function updateProject(
  projectId: string,
  userId: string,
  data: Partial<Pick<typeof projects.$inferInsert, "name">>
) {
  const [updated] = await db
    .update(projects)
    .set({ ...data, updatedAt: new Date() })
    .where(and(eq(projects.id, projectId), eq(projects.userId, userId)))
    .returning();

  if (!updated) throw new AppError("Project not found", 404);
  return updated;
}
```

**Why include `userId` in every update WHERE clause?** Prevents horizontal
privilege escalation. If you only check `eq(projects.id, projectId)`, a user who
knows another user's project ID can overwrite it.

**Do not** use raw SQL (`db.run("UPDATE ...")`) for application queries. Raw SQL
bypasses TypeScript type checking and is harder to refactor when schema changes.
Exception: complex analytical queries with CTEs where the query builder becomes
unreadable.

---

## Authentication (Lucia v3)

### Setup

```typescript
// src/lib/auth.ts
import { Lucia, TimeSpan } from "lucia";
import { LibSQLAdapter } from "@lucia-auth/adapter-libsql";
import { db } from "@/db";
import { users, sessions } from "@/db/schema";

const adapter = new LibSQLAdapter(db.$client, {
  user: "users",
  session: "sessions",
});

export const lucia = new Lucia(adapter, {
  sessionExpiresIn: new TimeSpan(30, "d"),
  sessionCookie: {
    attributes: {
      secure: process.env.NODE_ENV === "production",
    },
  },
  getUserAttributes: (attributes) => ({
    email: attributes.email,
  }),
});

declare module "lucia" {
  interface Register {
    Lucia: typeof lucia;
    DatabaseUserAttributes: { email: string };
  }
}

// Helper for Server Components and Server Actions
export async function getSession() {
  const { cookies } = await import("next/headers");
  const sessionId = cookies().get(lucia.sessionCookieName)?.value ?? null;
  if (!sessionId) return { user: null, session: null };
  return lucia.validateSession(sessionId);
}
```

### Auth Guard Pattern

```typescript
// app/(dashboard)/layout.tsx
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, session } = await getSession();

  if (!user || !session) {
    redirect("/login");
  }

  return <div>{children}</div>;
}
```

**Do not** check auth in individual Server Actions or page components when a
layout already does it. **Why?** Defense in depth is good; duplication is a
maintenance hazard. The layout is the single choke point.

**Do not** use `useSession()` client-side hooks to gate UI. The server layout
redirect is the authoritative auth check. Client-side auth state is for
UI polish only (showing username, etc.).

### Sign Up Flow

```typescript
// app/(auth)/signup/actions.ts
"use server";

import { z } from "zod";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { Argon2id } from "oslo/password";
import { lucia } from "@/lib/auth";
import { db } from "@/db";
import { users } from "@/db/schema";
import { createId } from "@paralleldrive/cuid2";
import { AppError } from "@/lib/errors";

const signUpSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(72), // Argon2id max is 72 bytes
});

export async function signUp(formData: FormData) {
  const parsed = signUpSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });

  if (!parsed.success) {
    return { error: "Invalid email or password format" };
  }

  const { email, password } = parsed.data;

  // Check if user exists — return same error for security (no user enumeration)
  const existing = await db.query.users.findFirst({
    where: (u, { eq }) => eq(u.email, email),
  });
  if (existing) {
    return { error: "Could not create account. Try logging in." };
  }

  const hashedPassword = await new Argon2id().hash(password);
  const userId = createId();

  await db.insert(users).values({ id: userId, email, hashedPassword });

  const session = await lucia.createSession(userId, {});
  const sessionCookie = lucia.createSessionCookie(session.id);
  (await cookies()).set(
    sessionCookie.name,
    sessionCookie.value,
    sessionCookie.attributes
  );

  redirect("/dashboard");
}
```

**Why Argon2id?** It's resistant to GPU cracking and side-channel attacks.
bcrypt is not the right choice for new projects in 2025.

**Why max 72 bytes on password?** Argon2id truncates at 72 bytes. Passwords
longer than this give false security. Zod enforces this explicitly.

---

## Error Handling

### AppError

```typescript
// src/lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number = 400,
    public readonly code?: string
  ) {
    super(message);
    this.name = "AppError";
  }

  toJSON() {
    return {
      error: this.message,
      statusCode: this.statusCode,
      code: this.code,
    };
  }
}

export function isAppError(err: unknown): err is AppError {
  return err instanceof AppError;
}
```

### Error in Server Actions

```typescript
// In a Server Action
export async function someAction(formData: FormData) {
  try {
    const result = await someService.doThing();
    return { data: result };
  } catch (err) {
    if (isAppError(err)) {
      return { error: err.message }; // Safe to show to user
    }
    console.error("Unexpected error in someAction:", err);
    return { error: "Something went wrong. Please try again." };
  }
}
```

**Do not** let raw errors propagate to the client. Raw errors expose stack traces,
internal paths, and database schema names. Always catch and return a sanitized
message.

**Do not** use `try/catch` around every single line. Use it at the boundary
(Server Action, route handler) not inside service functions. Let service
functions throw — the boundary catches.

---

## Component Patterns

### Server Components (default)

```tsx
// app/(dashboard)/projects/page.tsx
import { getSession } from "@/lib/auth";
import { getProjectsByUser } from "@/services/project.service";

// No "use client" — this runs on the server
export default async function ProjectsPage() {
  const { user } = await getSession();
  // user is guaranteed non-null by the layout auth guard above this page

  const projects = await getProjectsByUser(user!.id);

  return (
    <main>
      <h1>Projects</h1>
      {projects.map((p) => (
        <div key={p.id}>{p.name}</div>
      ))}
    </main>
  );
}
```

**Do not** add `"use client"` to a page component to fetch data. Server
Components fetch data directly — no `useEffect`, no loading spinners for
initial page data.

### Client Components (forms + interactivity)

```tsx
// components/forms/create-project-form.tsx
"use client";

import { useActionState } from "react";
import { createProjectAction } from "@/app/(dashboard)/projects/actions";

export function CreateProjectForm() {
  const [state, action, isPending] = useActionState(
    createProjectAction,
    null
  );

  return (
    <form action={action}>
      <input name="name" placeholder="Project name" required />
      {state?.error && <p className="text-red-500">{state.error}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Creating…" : "Create Project"}
      </button>
    </form>
  );
}
```

**Why `useActionState` not `useState` + `fetch`?** Server Actions with
`useActionState` give you progressive enhancement (works without JavaScript),
automatic form state, and no manual loading state boilerplate.

**Do not** use `fetch('/api/...')` from a Client Component when a Server Action
can do the job. API routes are for external webhooks and integrations, not
internal UI data mutations.

### Prop Types

```typescript
// Always define props as a type, not inline
type ButtonProps = {
  label: string;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
};

export function Button({ label, onClick, variant = "primary", disabled }: ButtonProps) {
  // ...
}
```

**Do not** use `React.FC<Props>`. Use plain function declarations.
**Why?** `React.FC` includes an implicit `children` prop that is usually
unintended and hides type errors.

---

## Data Fetching Patterns

### In Server Components: direct service calls

```tsx
// Direct — no HTTP round trip
const projects = await getProjectsByUser(userId);
```

### In Server Actions: Zod validation first

```typescript
"use server";

import { z } from "zod";

const schema = z.object({
  name: z.string().min(1).max(100).trim(),
});

export async function createProjectAction(
  _prev: unknown,
  formData: FormData
) {
  const parsed = schema.safeParse({ name: formData.get("name") });
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }
  // ...
}
```

**Never** call a service function without validating input first.
**Why?** `formData.get()` returns `string | File | null`. Passing raw FormData
values directly to Drizzle inserts null/File into database columns silently.

### Caching

```typescript
// Opt into Next.js caching explicitly
import { unstable_cache } from "next/cache";

export const getCachedProjectsByUser = unstable_cache(
  async (userId: string) => getProjectsByUser(userId),
  ["projects-by-user"],
  { revalidate: 60, tags: ["projects"] }
);
```

**Do not** cache by default. Add caching when profiling shows a genuine
bottleneck. Premature caching introduces stale data bugs.

---

## SQL / Migration Conventions

1. **One schema file** — all tables in `src/db/schema.ts`. No splitting by domain.
2. **Column naming** — `snake_case` in the database, always.
3. **Migration naming** — let `drizzle-kit generate` name them (`0001_...sql`).
   Never rename migration files.
4. **Never delete migration files** — they are the audit trail of every schema
   change. Even if you revert a feature, keep the migration.
5. **For destructive changes** (column rename, type change), write two migrations:
   one to add the new column, one to drop the old after the deploy confirms success.
6. **Indexes** — add indexes to any column that appears in a WHERE clause on
   a table with more than 10K expected rows.
7. **No multi-statement transactions in migrations** — libSQL/Turso does not
   support interactive transactions in embedded replicas. Use single statements.

---

## Naming Conventions

| Thing | Convention | Example |
|-------|------------|---------|
| Files/folders | `kebab-case` | `create-project-form.tsx` |
| Components | `PascalCase` | `CreateProjectForm` |
| Functions | `camelCase` | `getProjectsByUser` |
| Types/Interfaces | `PascalCase` | `ProjectWithOwner` |
| DB table names | `snake_case` plural | `projects`, `user_sessions` |
| DB column names | `snake_case` | `created_at`, `hashed_password` |
| Env vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |
| Route segments | `kebab-case` | `/user-settings` |
| Server Actions | `*Action` suffix | `createProjectAction` |
| Service functions | verb + noun | `getProjectsByUser`, `deleteProject` |

---

## Dev Commands

```bash
pnpm dev             # Start Next.js dev server (port 3000)
pnpm build           # Production build
pnpm start           # Run production build locally
pnpm test            # Run Vitest unit tests
pnpm test:e2e        # Run Playwright end-to-end tests
pnpm db:generate     # Generate Drizzle migration from schema changes
pnpm db:migrate      # Apply pending migrations to local database
pnpm db:studio       # Open Drizzle Studio (visual DB browser)
pnpm typecheck       # Run tsc --noEmit (no output files)
pnpm lint            # Run ESLint
```

**Always run `pnpm typecheck` before submitting a PR.** Do not leave `@ts-ignore`
or `as any` in production code. If TypeScript can't infer the type, add an
explicit annotation.

---

## Testing

### Unit Tests (Vitest + in-memory SQLite)

```typescript
// tests/services/project.service.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { db } from "@/db";
import { users } from "@/db/schema";
import { createProject, getProjectsByUser } from "@/services/project.service";

// Drizzle in-memory — schema is applied at test startup
// Configure in vitest.setup.ts: applyMigrations(db)

describe("project service", () => {
  let userId: string;

  beforeEach(async () => {
    // Clean state for each test
    userId = "test-user-1";
    await db.insert(users).values({ id: userId, email: "test@example.com" });
  });

  it("creates a project and returns it", async () => {
    const project = await createProject(userId, "My App");
    expect(project.name).toBe("My App");
    expect(project.userId).toBe(userId);
    expect(project.id).toMatch(/^[a-z0-9]+$/); // cuid2 pattern
  });

  it("getProjectsByUser returns only that user's projects", async () => {
    await createProject(userId, "App A");
    await createProject(userId, "App B");

    const projects = await getProjectsByUser(userId);
    expect(projects).toHaveLength(2);
    expect(projects.every((p) => p.userId === userId)).toBe(true);
  });
});
```

**Do not** mock the database in unit tests. Use the in-memory SQLite database.
**Why?** Mocking `db.select()` tests nothing. In-memory SQLite is fast enough
(< 50ms per test) and exercises real query logic.

**Do not** share database state between tests. Use `beforeEach` to insert only
the rows needed for that test, and configure the DB to reset between tests.

### E2E Tests (Playwright)

```typescript
// tests/e2e/signup.spec.ts
import { test, expect } from "@playwright/test";

test("user can sign up and reach the dashboard", async ({ page }) => {
  await page.goto("/signup");
  await page.getByLabel("Email").fill("test@example.com");
  await page.getByLabel("Password").fill("securepassword123");
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL("/dashboard");
});
```

**Use `getByRole` and `getByLabel` selectors, not CSS selectors or test IDs.**
**Why?** Role-based selectors test accessibility attributes. They break when
accessibility is broken, which is what we want.

---

## What We Don't Do (and Why)

### No `pages/` directory

We use App Router exclusively. Mixing App Router and Pages Router causes subtle
hydration bugs and makes middleware confusing.

### No Redux, Zustand, or global state stores

Server Components handle most data fetching. `useActionState` handles form state.
`useState` handles local UI state. Global state stores solve a problem App Router
largely doesn't have.

If a page needs shared state between multiple components, lift state to their
common Server Component ancestor and pass as props.

### No API routes for internal CRUD

`/api/projects` that fetches from the database and returns JSON is unnecessary
when a Server Component or Server Action can query the database directly. API
routes add a network round trip, serialization overhead, and a surface for auth
bugs.

Use API routes only for: webhooks from external services (Stripe, GitHub),
endpoints consumed by mobile apps, and routes that need custom HTTP response
headers.

### No `async/await` in Client Components for data fetching

Client Components do not fetch data on mount with `useEffect(() => { fetch(...) })`.
Data comes from Server Components (initial load) or Server Actions (mutations).
For SWR-style real-time data, use React Query with Server Action as the fetcher.

### No `.env.local` secrets in version control

`.env.local` is in `.gitignore`. Never commit real secrets. Use a secrets manager
or the hosting provider's environment variable UI.

### No `any` type

If you can't figure out the type, use `unknown` and narrow it. `any` turns off
the type checker on that variable and all variables it touches.

### No `db:push` in staging or production

`drizzle-kit push` syncs the database to the schema without generating a migration.
It can silently drop columns or change types. Only `db:migrate` runs in
non-development environments.

### No direct cookie manipulation outside `src/lib/auth.ts`

Lucia manages session cookies. If you need to read auth state, use `getSession()`.
Do not import `cookies()` from `next/headers` to read/set session cookies
directly — you will break the Lucia session lifecycle.

---

## Common Patterns

### Redirect after Server Action

```typescript
"use server";
import { redirect } from "next/navigation";

export async function deleteProjectAction(formData: FormData) {
  const projectId = formData.get("projectId") as string;
  await deleteProject(projectId, userId);
  redirect("/dashboard"); // Never inside try/catch — redirect throws internally
}
```

**Do not** put `redirect()` inside a `try/catch` block. `redirect()` works by
throwing a special Next.js error. If you catch it, the redirect never happens.

### Revalidating Cache After Mutations

```typescript
import { revalidateTag } from "next/cache";

export async function createProjectAction(formData: FormData) {
  const project = await createProject(userId, name);
  revalidateTag("projects"); // Clears cached data with this tag
  return { data: project };
}
```

### Email Sending

```typescript
// src/lib/email.ts
import { Resend } from "resend";
import { env } from "@/env";

const resend = new Resend(env.RESEND_API_KEY);

export async function sendWelcomeEmail(to: string, name: string) {
  const { error } = await resend.emails.send({
    from: `${env.NEXT_PUBLIC_APP_NAME} <noreply@yourdomain.com>`,
    to,
    subject: `Welcome to ${env.NEXT_PUBLIC_APP_NAME}`,
    text: `Hi ${name}, thanks for signing up!`,
  });

  if (error) {
    console.error("Failed to send welcome email:", error);
    // Don't throw — email failure should not block sign-up
  }
}
```

**Why not throw on email failure?** Email is non-critical for the user flow.
Log the error, alert the team via monitoring, but don't fail the sign-up.

---

## TypeScript Strict Patterns

`tsconfig.json` has `"strict": true`. This enables:

- `noImplicitAny` — every variable has a type
- `strictNullChecks` — `null` and `undefined` are not assignable to other types
- `strictFunctionTypes` — function parameter types are checked contravariantly

**Do not** disable strict mode. **Do not** add `// @ts-expect-error` without a
comment explaining why.

```typescript
// Narrowing unknown errors properly
try {
  await riskyOperation();
} catch (err) {
  if (err instanceof Error) {
    console.error(err.message);
  } else {
    console.error("Unknown error", err);
  }
}
```

---

## When to Ask Before Implementing

Come back with a question if you encounter any of these:

- **A schema change** — even adding a column. We discuss before generating a migration.
- **A new third-party service** — every new integration has operational cost.
- **Routing changes** — moving a page changes URLs, potentially breaking links.
- **Auth flow changes** — session bugs can log out all users simultaneously.
- **Performance optimization** — profile first. "This might be slow" is not
  enough reason to add caching, indexes, or connection pooling.
- **Any `db:push`** — confirm this is a local dev environment first.

---

## Deployment

### Vercel (recommended)

1. Connect GitHub repo
2. Set env vars in Vercel dashboard
3. `DATABASE_URL` points to Turso production database
4. Build command: `pnpm build && pnpm db:migrate`
5. Zero-downtime: Turso migrations are additive by default

### Railway / Fly.io

Same pattern: run `pnpm db:migrate` as part of the release command before the
new version starts serving traffic.

**Do not** run migrations from within the Next.js application startup code.
**Why?** If two instances start simultaneously, both run migrations and you get
locking errors or double-applied migrations.

---

## Security Checklist

Before any PR:

- [ ] All Server Actions validate input with Zod
- [ ] All DB mutations include userId in WHERE clause (ownership check)
- [ ] No secrets in code — only via `env.*`
- [ ] Auth-gated pages are inside `(dashboard)/` route group
- [ ] Passwords hashed with Argon2id
- [ ] Sessions use HttpOnly, SameSite=Lax cookies (Lucia default)
- [ ] No user-supplied values interpolated directly into SQL strings
- [ ] File uploads (if any) validate file type by magic bytes, not extension

---

*This CLAUDE.md was tested by creating a fresh Next.js 15 + Turso project,
pasting it as the first file, and verifying that Claude Code could implement
sign-up, project CRUD, and email without asking clarifying questions about
architecture or conventions.*
