# CLAUDE.md — Next.js 15 + SQLite SaaS

> This file is read by AI assistants working on this codebase. Every rule here
> exists because we got burned by the alternative. If you disagree with a rule,
> open a discussion — don't just ignore it.

---

## Stack & Versions

| Layer        | Choice              | Why                                                                 |
|--------------|---------------------|---------------------------------------------------------------------|
| Framework    | Next.js 15 (App Rtr)| Server Components eliminate client waterfalls; RSC cuts bundle size  |
| Language     | TypeScript 5.x      | Strict mode on; `noUncheckedIndexedAccess` enabled                  |
| Database     | SQLite + better-sqlite3 | Zero-config, single-file, synchronous API — perfect for SaaS MVP  |
| ORM          | Drizzle ORM         | Type-safe SQL that doesn't abstract away SQLite's strengths         |
| Styling      | Tailwind CSS 4      | Co-located styles, no naming bikeshedding, purges unused CSS        |
| Validation   | Zod                 | Runtime + static types from one schema; API boundary enforcement    |
| Auth         | Better-Auth / Lucia | Session-based, no JWTs (see anti-patterns)                          |
| Package mgr  | pnpm                | Strict deps, fast installs, disk-efficient                          |

### Dev Commands

```bash
pnpm dev              # Start Next.js dev server (Turbopack)
pnpm build            # Production build (catches type errors + dead code)
pnpm lint             # ESLint + Prettier check
pnpm lint:fix         # Auto-fix what we can
pnpm db:generate      # Generate Drizzle migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:push          # Push schema directly (dev only — never in CI)
pnpm db:studio        # Open Drizzle Studio for visual DB inspection
pnpm db:seed          # Run seed script (idempotent — safe to re-run)
pnpm test             # Run Vitest suite
pnpm test:e2e         # Run Playwright E2E tests
pnpm typecheck        # `tsc --noEmit` — run before every PR
```

**Rule:** `pnpm db:push` is for local prototyping only. Once a migration exists
in `drizzle/migrations/`, it is immutable. We never edit past migrations — we
write corrective migrations instead.

---

## Folder Structure

```
src/
├── app/
│   ├── (auth)/               # Route group: login, register, forgot-password
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── register/
│   │   │   └── page.tsx
│   │   └── layout.tsx        # Auth layout (centered card, no sidebar)
│   ├── (dashboard)/          # Route group: authenticated app shell
│   │   ├── layout.tsx        # Dashboard layout (sidebar + topbar)
│   │   ├── page.tsx          # /dashboard home
│   │   ├── settings/
│   │   │   ├── page.tsx
│   │   │   └── actions.ts    # Server Actions for settings forms
│   │   └── teams/
│   │       ├── page.tsx
│   │       └── [teamId]/
│   │           ├── page.tsx
│   │           ├── members/
│   │           └── settings/
│   └── api/
│       └── webhooks/         # External webhooks (Stripe, etc.)
│           └── stripe/
│               └── route.ts
├── components/
│   ├── ui/                   # Headless, reusable, zero business logic
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   └── data-table.tsx
│   └── features/             # Feature-specific, may have business logic
│       ├── auth/
│       │   ├── login-form.tsx
│       │   └── register-form.tsx
│       ├── dashboard/
│       │   └── sidebar.tsx
│       └── teams/
│           ├── team-list.tsx
│           └── invite-member-dialog.tsx
├── lib/
│   ├── db/
│   │   ├── index.ts          # Singleton Drizzle client (see below)
│   │   ├── schema.ts         # All table definitions
│   │   ├── queries/          # Reusable query functions (not raw .select() calls)
│   │   │   ├── users.ts
│   │   │   └── teams.ts
│   │   └── migrations/       # Symlink or generated — actual files in /drizzle
│   ├── auth/
│   │   ├── index.ts          # Auth client export
│   │   ├── middleware.ts      # Auth guard utilities
│   │   └── session.ts        # Session helpers
│   ├── errors.ts             # Typed error classes (AppError, NotFoundError, etc.)
│   ├── constants.ts          # App-wide constants (NOT env vars — those go in env.ts)
│   ├── env.ts                # Zod-validated env vars (fails fast on missing vars)
│   └── utils/
│       ├── cn.ts             # clsx + twMerge helper
│       ├── format.ts         # Date/number formatters
│       └── slug.ts           # Slug generation utilities
├── hooks/                    # Custom React hooks (client-side only)
│   ├── use-debounce.ts
│   └── use-media-query.ts
├── types/                    # Shared TypeScript types
│   └── index.ts
└── styles/                   # Global styles (minimal — prefer Tailwind)
    └── globals.css
drizzle/
├── drizzle.config.ts         # Drizzle Kit config
└── migrations/               # Generated SQL migrations (IMMUTABLE)
    ├── 0000_initial.sql
    └── meta/
        └── _journal.json
```

### Why This Structure

- **Route groups `(auth)` and `(dashboard)`** — Keeps layouts separate without
  affecting URLs. No `/auth/login` — just `/login`.
- **`components/ui/` vs `components/features/`** — UI components are dumb and
  reusable. Feature components know about your domain. Mixing them creates
  spaghetti imports.
- **`lib/db/queries/`** — Centralizes DB access. No component or route handler
  should call `db.select()` directly. Every query goes through a named function
  here. This is the single most important rule for testability.
- **`lib/env.ts`** — Validates all env vars at startup with Zod. If a required
  var is missing, the app crashes at boot, not at 3 AM when a user hits a
  specific endpoint.

---

## Naming Conventions

| What                  | Convention           | Example                   | Reason                                         |
|-----------------------|----------------------|---------------------------|------------------------------------------------|
| Files                 | kebab-case           | `user-profile.tsx`        | Consistent with URL segments; no OS portability issues |
| React components      | PascalCase           | `UserProfile`             | Distinguishes components from utilities in JSX |
| DB tables             | snake_case           | `user_profiles`           | SQLite/Postgres convention; Drizzle generates these by default |
| DB columns            | snake_case           | `created_at`              | Same as tables; keeps SQL readable             |
| API routes            | kebab-case           | `/api/user-profiles`      | URL-friendly, REST convention                  |
| Server Actions        | camelCase with verb  | `createTeam`, `updateUser`| Readable in forms; verb-first for clarity      |
| TypeScript types      | PascalCase           | `UserProfile`             | Interface/type distinction from values         |
| Zod schemas           | camelCase + Schema   | `createUserSchema`        | Pairs with inferred type: `CreateUser`         |
| Constants             | SCREAMING_SNAKE      | `MAX_TEAM_MEMBERS`        | Signals "don't mutate" at a glance             |
| Boolean variables     | is/has/can prefix    | `isLoading`, `hasError`   | Reads naturally in conditionals                |

---

## Database Rules

### Schema Definition

All tables live in `src/lib/db/schema.ts`. One file. We don't split schemas
per-feature because SQLite is a single database — seeing all tables at once
prevents naming collisions and makes relationships obvious.

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});
```

### Column Rules

1. **Always include `created_at` and `updated_at`** — You will need them for
   debugging, audit trails, and cache invalidation. No exceptions.
2. **Use `text` for IDs** — UUIDs as text, not integers. Auto-increment IDs
   leak business metrics and cause merge conflicts in distributed setups.
3. **Use `integer` with `mode: "timestamp"` for dates** — SQLite has no native
   datetime type. Storing as integer (Unix epoch) is sortable and compact.
4. **Default values at the DB level** — Use `.$defaultFn()` in Drizzle, not
   application-level defaults. The DB is the source of truth.

### Migration Workflow

```bash
# 1. Edit schema.ts
# 2. Generate migration
pnpm db:generate
# 3. Review the generated SQL in drizzle/migrations/
# 4. Apply it
pnpm db:migrate
# 5. Commit BOTH schema.ts AND the migration files
```

**Immutability rule:** Once a migration file is committed, it is never edited.
If a migration has a bug, write a new corrective migration. Editing past
migrations breaks anyone who already applied them.

**Naming rule:** Drizzle auto-names migrations with timestamps. Don't rename
them. The `_journal.json` tracks which migrations have been applied.

### Query Patterns

```typescript
// src/lib/db/queries/users.ts
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export async function getUserById(id: string) {
  return db.query.users.findFirst({
    where: eq(users.id, id),
  });
}

export async function getUsersByTeam(teamId: string) {
  return db.query.users.findMany({
    where: eq(users.teamId, teamId),
    orderBy: (users, { desc }) => [desc(users.createdAt)],
  });
}

export async function createUser(data: typeof users.$inferInsert) {
  return db.insert(users).values(data).returning();
}
```

**Why named query functions?** Three reasons:
1. **Testability** — Mock the function, not the ORM chain.
2. **Reusability** — Same query in a page, action, and API route.
3. **Readability** — `getUserById(id)` tells you intent; `db.query.users.findFirst(...)` tells you implementation.

---

## Component Patterns

### Server Components (Default)

Every component is a Server Component unless it explicitly needs interactivity.
This is the opposite of the old mental model — you opt *in* to client, not out.

```typescript
// src/components/features/teams/team-list.tsx
import { getTeamsByUser } from "@/lib/db/queries/teams";

export async function TeamList({ userId }: { userId: string }) {
  const teams = await getTeamsByUser(userId);

  if (teams.length === 0) {
    return <p className="text-muted-foreground">No teams yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {teams.map((team) => (
        <li key={team.id} className="rounded-lg border p-4">
          {team.name}
        </li>
      ))}
    </ul>
  );
}
```

### Client Components

Only add `"use client"` when the component needs:
- `useState`, `useReducer`, `useContext`
- `useEffect` or `useLayoutEffect`
- Browser APIs (`window`, `document`, `localStorage`)
- Event handlers (`onClick`, `onChange`)
- Third-party libraries that use hooks

```typescript
// src/components/features/teams/invite-member-dialog.tsx
"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { inviteMember } from "@/app/(dashboard)/teams/actions";

export function InviteMemberDialog({ teamId }: { teamId: string }) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");

  async function handleInvite() {
    await inviteMember({ teamId, email });
    setOpen(false);
    setEmail("");
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Invite Member</Button>
      </DialogTrigger>
      <DialogContent>
        {/* form fields */}
      </DialogContent>
    </Dialog>
  );
}
```

### Component Rules

1. **One component per file** — Exception: tiny helper components (< 10 lines)
  that are only used by the parent can be in the same file.
2. **Props interface above component** — Keep types close to usage. If the
   props interface grows past 8 fields, extract a subset into a shared type.
3. **Use `forwardRef` only when building `ui/` components** that need to
   compose with Radix or similar. Feature components almost never need it.
4. **Colocate styles** — Tailwind classes go directly on JSX. Don't create
   separate CSS modules or styled-components for components.
5. **Server → Client boundary** — Pass serializable data (strings, numbers,
   plain objects) across the boundary. Never pass functions, Dates, or
   class instances.

### Data Fetching

```
Page (Server Component) ──→ Query function ──→ Drizzle ──→ SQLite
       │
       └──→ Renders <ClientComponent data={serializableData} />
```

**We never fetch data in `useEffect`.** Data fetching happens in:
1. **Server Components** (preferred) — Direct DB calls via query functions.
2. **Server Actions** — For mutations triggered by user interaction.
3. **API Routes** — Only for external consumers (webhooks, mobile apps).

### Server Actions

```typescript
// src/app/(dashboard)/teams/actions.ts
"use server";

import { z } from "zod";
import { db } from "@/lib/db";
import { teams } from "@/lib/db/schema";
import { requireAuth } from "@/lib/auth/middleware";
import { revalidatePath } from "next/cache";

const createTeamSchema = z.object({
  name: z.string().min(2).max(50),
});

export async function createTeam(formData: FormData) {
  const user = await requireAuth();

  const parsed = createTeamSchema.safeParse({
    name: formData.get("name"),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  const [team] = await db
    .insert(teams)
    .values({ name: parsed.data.name, ownerId: user.id })
    .returning();

  revalidatePath("/teams");
  return { data: team };
}
```

**Action rules:**
- Always validate with Zod — never trust form data.
- Always require auth — even if the page checks it too.
- Always `revalidatePath` — stale data is worse than slow data.
- Return `{ data }` or `{ error }` — never throw in actions.

---

## Environment Variables

```typescript
// src/lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string(),
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_"),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
});

export const env = envSchema.parse(process.env);
```

**Rules:**
- Import `env` from `@/lib/env`, never access `process.env` directly.
- The app crashes at boot if a variable is missing — this is intentional.
- All secrets live in `.env.local` (gitignored). `.env.example` has the keys
  with placeholder values.

---

## What We Don't Do (And Why)

### ❌ Don't use `any`

If you need `any`, you don't understand the type yet. Use `unknown` and narrow
with type guards, or ask for help. `any` disables TypeScript's entire value
proposition and infects every type it touches.

```typescript
// BAD
function process(data: any) { ... }

// GOOD
function process(data: unknown) {
  if (typeof data === "string") { ... }
}
```

### ❌ Don't put business logic in components

Components render UI. That's it. Business logic (validation, authorization,
transformations) lives in:
- `lib/` for utilities
- `lib/db/queries/` for data access
- Server Actions for mutations
- `lib/errors.ts` for error handling

If you copy-paste a component's logic into another component, the logic was
in the wrong place.

### ❌ Don't use `useEffect` for data fetching

`useEffect` + `fetch` = loading spinners, stale data, race conditions, and
waterfalls. Server Components give you the data before the HTML ships. Use them.

```typescript
// BAD
"use client";
useEffect(() => {
  fetch("/api/teams").then(r => r.json()).then(setTeams);
}, []);

// GOOD
async function TeamList() {
  const teams = await getTeamsByUser(userId); // Direct DB call
  return <ul>{/* render */}</ul>;
}
```

### ❌ Don't store sensitive data in client state

If it's in `useState`, it's in the client bundle. Tokens, passwords, API keys,
and PII belong on the server. Pass only what the client needs to render.

### ❌ Don't use JWTs for session management

JWTs can't be revoked, grow large with claims, and encourage storing data
client-side. Use opaque session tokens stored in the DB. SQLite makes session
lookups sub-millisecond.

### ❌ Don't use `export default`

Named exports are searchable, refactorable, and prevent naming mismatches
between import and export. One export per file keeps things unambiguous.

```typescript
// BAD
export default function Button() { ... }

// GOOD
export function Button() { ... }
```

### ❌ Don't create barrel exports (`index.ts` that re-exports everything)

Barrel files cause:
- Slower builds (bundler must resolve the entire barrel)
- Circular dependency traps
- Unclear import paths (am I importing from the file or the barrel?)

Import directly from the source file.

### ❌ Don't abstract too early

Don't create `BaseEntity`, `GenericRepository`, or `AbstractService` classes.
Write the concrete implementation first. Extract to a shared pattern only when
you have 3+ identical usages. Premature abstraction is harder to undo than
duplication.

### ❌ Don't use `try/catch` without logging

Swallowed errors are the #1 cause of "it works on my machine" bugs. Every
catch block must either:
- Re-throw as a typed error (see `lib/errors.ts`)
- Log the error
- Return an error response to the user

```typescript
// BAD
try {
  await createUser(data);
} catch (e) {
  return { error: "Something went wrong" }; // WHERE DID THE ERROR GO?
}

// GOOD
try {
  const user = await createUser(data);
  return { data: user };
} catch (e) {
  if (e instanceof AppError) {
    return { error: e.message };
  }
  console.error("Unexpected error creating user:", e);
  return { error: "Internal server error" };
}
```

### ❌ Don't skip TypeScript strict mode

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,  // array[0] is T | undefined, not T
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

`noUncheckedIndexedAccess` prevents the most common runtime crash in
TypeScript: accessing an array element that might be undefined.

---

## Git Workflow

- **Branch naming:** `feat/short-description`, `fix/short-description`, `chore/short-description`
- **Commit messages:** Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR checklist:**
  - [ ] `pnpm typecheck` passes
  - [ ] `pnpm lint` passes
  - [ ] No new `// @ts-ignore` or `// eslint-disable` comments
  - [ ] Migration files included if schema changed
  - [ ] New env vars documented in `.env.example`

---

## Performance Rules

1. **Images** — Always use `next/image`. Always set `width`, `height`, and `alt`.
2. **Fonts** — Use `next/font`. Self-hosted, zero layout shift.
3. **Dynamic imports** — Use `next/dynamic` for heavy client components
   (charts, editors, maps) below the fold.
4. **Streaming** — Wrap slow data fetches in `<Suspense>` with a skeleton
   fallback. The page shell renders instantly.
5. **SQLite pragmas** — Enable WAL mode for concurrent reads:
   ```typescript
   const db = new Database("app.db");
   db.pragma("journal_mode = WAL");
   db.pragma("foreign_keys = ON");
   ```

---

## Error Handling

```typescript
// src/lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export class NotFoundError extends AppError {
  constructor(entity: string, id: string) {
    super(`${entity} not found: ${id}`, "NOT_FOUND", 404);
  }
}

export class UnauthorizedError extends AppError {
  constructor() {
    super("Unauthorized", "UNAUTHORIZED", 401);
  }
}

export class ValidationError extends AppError {
  constructor(public fields: Record<string, string[]>) {
    super("Validation failed", "VALIDATION_ERROR", 400);
  }
}
```

Use these in query functions, server actions, and API routes. Never throw
raw `new Error()` in application code — it lacks context.

---

## Quick Reference: Creating a New Feature

Here's the checklist when adding a new feature (e.g., "Billing"):

1. **Schema** — Add table to `src/lib/db/schema.ts`
2. **Migration** — `pnpm db:generate` → review → `pnpm db:migrate`
3. **Queries** — Add query functions in `src/lib/db/queries/billing.ts`
4. **Validation** — Add Zod schemas in `src/lib/db/queries/billing.ts` or
   `src/lib/validators/billing.ts`
5. **Page** — Create `src/app/(dashboard)/billing/page.tsx` (Server Component)
6. **Actions** — Create `src/app/(dashboard)/billing/actions.ts` for mutations
7. **Components** — Feature components in `src/components/features/billing/`
8. **Tests** — Unit tests in `src/__tests__/billing.test.ts`
9. **E2E** — If critical path, add Playwright test in `e2e/billing.spec.ts`

---

*Last updated: 2025-06. If this file is more than 6 months old, review the
stack versions and update any deprecated patterns.*
