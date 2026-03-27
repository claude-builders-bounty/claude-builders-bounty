# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the single source of truth for how code is written in this project.
Follow every rule. If a rule seems wrong for a specific case, leave a comment explaining why you deviated.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | Server Components by default, server actions, streaming |
| Runtime | Node.js | 22 LTS | Top-level await, native fetch, stable ESM |
| Language | TypeScript | 5.x | Strict mode, no `any` |
| Database | SQLite via better-sqlite3 | 11.x | Single-file, zero-ops, synchronous reads are fast |
| Migrations | Custom SQL files | — | No ORM migration layer; raw SQL is the migration |
| Auth | Auth.js (NextAuth v5) | 5.x | First-party App Router support, DB session strategy |
| Styling | Tailwind CSS | 4.x | Utility-first, no CSS modules, no styled-components |
| UI Components | shadcn/ui | latest | Copy-paste primitives, no version lock-in |
| Validation | Zod | 3.x | Runtime + static types from one schema |
| Package Manager | pnpm | 9.x | Strict, fast, disk-efficient |
| Linting | ESLint + Prettier | — | `next lint` handles framework rules |

### Version policy

Lock major versions in `package.json` with exact pins (`"next": "15.3.1"`, not `"^15.3.1"`).
Renovate or Dependabot handles upgrades — humans review diffs.

---

## Dev Commands

```bash
pnpm dev              # Start dev server on :3000
pnpm build            # Production build — fails on type errors
pnpm start            # Run production build locally
pnpm lint             # ESLint + Next.js rules
pnpm format           # Prettier write
pnpm format:check     # Prettier check (CI)
pnpm db:migrate       # Run pending migrations
pnpm db:seed          # Seed dev data
pnpm db:reset         # Drop + migrate + seed (dev only)
pnpm test             # Vitest unit/integration
pnpm test:e2e         # Playwright end-to-end
pnpm typecheck        # tsc --noEmit
```

CI runs: `typecheck` → `lint` → `test` → `build`. All four must pass.

---

## Project Structure

```
├── src/
│   ├── app/                    # Next.js App Router (routes + layouts)
│   │   ├── (auth)/             # Route group: login, signup, forgot-password
│   │   ├── (dashboard)/        # Route group: authenticated SaaS pages
│   │   │   ├── layout.tsx      # Sidebar + auth guard
│   │   │   ├── settings/
│   │   │   │   └── page.tsx
│   │   │   └── [teamId]/
│   │   │       └── page.tsx
│   │   ├── api/                # Route handlers (REST-style, minimal use)
│   │   │   └── webhooks/
│   │   │       └── stripe/
│   │   │           └── route.ts
│   │   ├── layout.tsx          # Root layout (html, body, providers)
│   │   ├── page.tsx            # Landing page
│   │   ├── not-found.tsx
│   │   └── error.tsx
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives (button, input, dialog…)
│   │   ├── forms/              # Form components with validation
│   │   ├── layouts/            # Sidebar, header, footer, nav
│   │   └── [feature]/          # Feature-scoped components (e.g., billing/)
│   ├── lib/
│   │   ├── db/
│   │   │   ├── index.ts        # DB connection singleton
│   │   │   ├── migrations/     # Sequential SQL files
│   │   │   ├── queries/        # Typed query functions grouped by table
│   │   │   └── seed.ts         # Dev seed data
│   │   ├── auth.ts             # Auth.js config
│   │   ├── validations/        # Zod schemas grouped by domain
│   │   └── utils.ts            # Pure utility functions (< 50 lines or split)
│   ├── actions/                # Server actions grouped by domain
│   │   ├── auth.ts
│   │   ├── team.ts
│   │   └── billing.ts
│   ├── hooks/                  # Client-side React hooks
│   ├── types/                  # Shared TypeScript types (not Zod — those go in validations/)
│   └── config/                 # App constants, feature flags, plan limits
├── public/                     # Static assets
├── drizzle/ or migrations/     # (if using Drizzle — otherwise src/lib/db/migrations/)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.local                  # Local secrets (never committed)
├── .env.example                # Template with dummy values (always committed)
└── next.config.ts
```

### Rules

- **One route = one `page.tsx`.** No logic in `page.tsx` beyond composing server components and fetching data.
- **Route groups `(name)/`** for shared layouts without adding URL segments.
- **`lib/` is framework-agnostic.** Nothing in `lib/` imports from `next/*` or React. Exception: `lib/auth.ts` which configures NextAuth.
- **`actions/` is the write layer.** All mutations go through server actions. Route handlers (`api/`) are only for webhooks, cron, and third-party callbacks.
- **`components/ui/` is untouched shadcn output.** Customize components by wrapping them in `components/[feature]/`, never by editing `ui/` files directly.

---

## Naming Conventions

### Files and directories

| Type | Convention | Example |
|---|---|---|
| Route files | `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` | Next.js convention, non-negotiable |
| Components | `kebab-case.tsx` | `team-switcher.tsx`, `billing-form.tsx` |
| Server actions | `kebab-case.ts` in `actions/` | `actions/team.ts` |
| Queries | `kebab-case.ts` in `lib/db/queries/` | `lib/db/queries/teams.ts` |
| Validations | `kebab-case.ts` in `lib/validations/` | `lib/validations/team.ts` |
| Hooks | `use-[name].ts` | `hooks/use-debounce.ts` |
| Types | `kebab-case.ts` | `types/team.ts` |
| Migrations | `NNNN_description.sql` | `0001_create_users.sql` |
| Tests | `[name].test.ts(x)` co-located or in `tests/` | `team-switcher.test.tsx` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL`, `STRIPE_SECRET_KEY` |

### Code identifiers

| Type | Convention | Example |
|---|---|---|
| React components | PascalCase | `TeamSwitcher`, `BillingForm` |
| Functions, variables | camelCase | `getTeamById`, `isActive` |
| Constants | SCREAMING_SNAKE (if truly constant) | `MAX_TEAM_MEMBERS` |
| Types/interfaces | PascalCase, no `I` prefix | `Team`, `CreateTeamInput` (not `ITeam`) |
| Zod schemas | camelCase + `Schema` suffix | `createTeamSchema` |
| DB columns | snake_case | `created_at`, `team_id` |
| URL paths | kebab-case | `/team-settings`, `/billing-history` |

### Boolean naming

Booleans start with `is`, `has`, `can`, `should`: `isActive`, `hasAccess`, `canEdit`.
DB columns: `is_active`, `has_completed`. No bare adjectives (`active`, `completed`).

---

## Database & SQL Conventions

### Connection

```typescript
// src/lib/db/index.ts
import Database from "better-sqlite3";
import path from "node:path";

const DB_PATH = process.env.DATABASE_URL ?? path.join(process.cwd(), "data", "app.db");

const db = new Database(DB_PATH, {
  // WAL mode: concurrent reads during writes, crash-safe
  // Set once on connection, not per-query
});

db.pragma("journal_mode = WAL");
db.pragma("busy_timeout = 5000");
db.pragma("synchronous = NORMAL");
db.pragma("cache_size = -64000"); // 64MB
db.pragma("foreign_keys = ON");

export default db;
```

**Why these pragmas:**
- `WAL` — readers never block writers; essential for a web server.
- `busy_timeout` — retry for 5s instead of throwing SQLITE_BUSY immediately.
- `synchronous = NORMAL` — safe with WAL, avoids fsync on every commit.
- `foreign_keys = ON` — SQLite disables them by default. Always enable.

### Migration rules

1. Migrations live in `src/lib/db/migrations/` as plain `.sql` files.
2. File naming: `NNNN_short_description.sql` — zero-padded four-digit sequence.
3. **Migrations are append-only.** Never edit a migration that has run in production. Write a new one.
4. Each migration file is a single transaction — wrap in `BEGIN; ... COMMIT;` if doing multiple statements.
5. Every table gets `id`, `created_at`, `updated_at`:

```sql
CREATE TABLE teams (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX idx_teams_owner_id ON teams(owner_id);
CREATE INDEX idx_teams_slug ON teams(slug);
```

### SQL style

- Keywords: `UPPERCASE` (`SELECT`, `FROM`, `WHERE`, `INSERT INTO`).
- Identifiers: `snake_case`, never quoted unless necessary.
- Always alias tables in joins: `FROM users u JOIN teams t ON t.owner_id = u.id`.
- **Every foreign key gets an index.** SQLite does not auto-index foreign keys.
- **Every column used in `WHERE` or `ORDER BY` frequently gets an index.** Add it in the same migration that creates the table.
- Use `TEXT` for IDs (UUIDs/nanoids), `TEXT` for ISO-8601 dates, `INTEGER` for booleans (0/1), `REAL` for money (store as cents `INTEGER` instead if precision matters).

### Query layer

Queries are typed functions, not raw SQL scattered through the codebase:

```typescript
// src/lib/db/queries/teams.ts
import db from "../index";
import type { Team, CreateTeamInput } from "@/types/team";

export function getTeamById(id: string): Team | undefined {
  return db.prepare("SELECT * FROM teams WHERE id = ?").get(id) as Team | undefined;
}

export function getTeamsByOwnerId(ownerId: string): Team[] {
  return db.prepare("SELECT * FROM teams WHERE owner_id = ?").all(ownerId) as Team[];
}

export function createTeam(input: CreateTeamInput): Team {
  const id = generateId();
  db.prepare(
    "INSERT INTO teams (id, name, slug, owner_id) VALUES (?, ?, ?, ?)"
  ).run(id, input.name, input.slug, input.ownerId);
  return getTeamById(id)!;
}
```

**Rules:**
- One file per table or tightly-related group of tables.
- Functions return typed results — cast with `as Type` at the boundary.
- Use `db.prepare()` — never string interpolation. Prepared statements prevent SQL injection and are cached by better-sqlite3.
- Write operations that need atomicity use `db.transaction()`.
- No query function accepts a raw SQL fragment as a parameter.

### Turso variant

If using Turso instead of better-sqlite3:
- Use `@libsql/client` instead of `better-sqlite3`.
- Connection is async — queries use `await`.
- Same SQL conventions apply. Same migration file format.
- Embedded replicas: use for read-heavy paths, primary for writes.

---

## Component Patterns

### Server vs. Client components

**Default to Server Components.** Only add `"use client"` when the component needs:
- `useState`, `useEffect`, `useReducer`, or other React hooks
- Browser APIs (`window`, `localStorage`, `IntersectionObserver`)
- Event handlers (`onClick`, `onChange`, `onSubmit`)
- Third-party client-only libraries

```
page.tsx (Server) → fetches data, passes as props
  └── data-table.tsx (Server) → renders static table markup
       └── sort-button.tsx (Client) → needs onClick
```

Push `"use client"` to the **leaf** components. Never mark a layout or page as client.

### Component file structure

```tsx
// components/teams/team-card.tsx

// 1. Imports (external, then internal, then types)
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { Team } from "@/types/team";

// 2. Types for this component (if not shared)
type TeamCardProps = {
  team: Team;
  onSelect?: (teamId: string) => void;
};

// 3. Component (named export, never default export)
export function TeamCard({ team, onSelect }: TeamCardProps) {
  return (
    <Card>
      <CardHeader>{team.name}</CardHeader>
      <CardContent>
        <p>Created {formatDate(team.createdAt)}</p>
      </CardContent>
    </Card>
  );
}
```

### Rules

- **Named exports only.** `export function TeamCard` — never `export default`. Named exports enable reliable auto-imports and grep-ability. The only exception is `page.tsx`, `layout.tsx`, and other Next.js route files which require default exports.
- **One component per file.** Small helper components used only within a single file are the one exception.
- **Props use `type`, not `interface`.** Types compose better with Zod inference (`z.infer<typeof schema>`). Interfaces are for extending — components rarely need that.
- **No barrel files (`index.ts`).** Import from the exact file: `import { TeamCard } from "@/components/teams/team-card"`. Barrel files break tree-shaking and create circular dependency traps.
- **No prop drilling beyond 2 levels.** If a prop passes through more than 2 components without being used, use composition (children/slots) or a context provider.

### Server actions

```typescript
// src/actions/team.ts
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createTeamSchema } from "@/lib/validations/team";
import { createTeam } from "@/lib/db/queries/teams";
import { getCurrentUser } from "@/lib/auth";

export async function createTeamAction(formData: FormData) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const parsed = createTeamSchema.safeParse({
    name: formData.get("name"),
    slug: formData.get("slug"),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await createTeam({ ...parsed.data, ownerId: user.id });

  revalidatePath("/dashboard");
  redirect("/dashboard");
}
```

**Rules:**
- Every action validates input with Zod. No exceptions.
- Every action checks auth before doing anything.
- Actions return `{ error }` for validation failures. They `redirect()` on success.
- Actions never return full database objects to the client — only what the UI needs.

### Forms

```tsx
// Client component using a server action
"use client";

import { useActionState } from "react";
import { createTeamAction } from "@/actions/team";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function CreateTeamForm() {
  const [state, action, isPending] = useActionState(createTeamAction, null);

  return (
    <form action={action}>
      <Input name="name" placeholder="Team name" />
      {state?.error?.name && <p className="text-sm text-destructive">{state.error.name}</p>}
      <Button type="submit" disabled={isPending}>
        {isPending ? "Creating…" : "Create Team"}
      </Button>
    </form>
  );
}
```

Use `useActionState` (React 19) for form state. No `useState` + `onSubmit` + manual fetch.

---

## Validation

All validation schemas live in `src/lib/validations/`. One file per domain.

```typescript
// src/lib/validations/team.ts
import { z } from "zod";

export const createTeamSchema = z.object({
  name: z.string().min(1, "Team name is required").max(50),
  slug: z.string().min(1).max(50).regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, and hyphens only"),
});

export const updateTeamSchema = createTeamSchema.partial();

export type CreateTeamInput = z.infer<typeof createTeamSchema>;
export type UpdateTeamInput = z.infer<typeof updateTeamSchema>;
```

**Rules:**
- Schemas are the source of truth for input types. Derive types with `z.infer<>` — never duplicate.
- Validate at the boundary: server actions, API route handlers, webhook handlers. Not inside query functions.
- One schema per operation (`createTeamSchema`, `updateTeamSchema`), not one god schema.

---

## Error Handling

- **Expected errors** (validation, not found, unauthorized): return structured error objects. Never throw.
- **Unexpected errors** (DB down, unhandled edge cases): let them throw. Next.js `error.tsx` catches them.
- **Never catch-and-ignore.** No empty `catch {}` blocks. Log or rethrow.
- **No try-catch around SQLite reads.** better-sqlite3 is synchronous and throws on genuine errors (corrupt DB, syntax errors). Those should crash loudly, not be swallowed.

---

## Auth Patterns

```typescript
// src/lib/auth.ts — export a helper, not the raw config
import { auth } from "./auth-config"; // NextAuth config

export async function getCurrentUser() {
  const session = await auth();
  if (!session?.user?.id) return null;
  return session.user;
}

export async function requireUser() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}
```

- Use `requireUser()` in server actions and protected pages.
- Use `getCurrentUser()` when auth is optional (landing page with conditional UI).
- **Never trust client-provided user IDs.** Always derive the user from the session.
- **Session strategy: `database`.** JWT sessions can't be revoked.

---

## Styling Rules

- **Tailwind only.** No CSS modules, no `styled-components`, no inline `style={}`.
- **Use `cn()` from `lib/utils` for conditional classes:**

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- **No magic numbers in Tailwind.** Use spacing scale (`p-4`, not `p-[17px]`). Arbitrary values signal a design system violation.
- **Dark mode: use CSS variables via shadcn theme.** No `dark:` prefix spam across components.
- **Responsive: mobile-first.** Default styles are mobile. Add `sm:`, `md:`, `lg:` for larger screens.

---

## What We Don't Do (and Why)

| Anti-pattern | Why we avoid it |
|---|---|
| **ORMs (Prisma, Drizzle ORM layer)** | SQLite is simple. Raw SQL with typed query functions gives full control, zero abstraction leakage, and no migration format lock-in. Query functions give us the same type safety at the boundary. |
| **Default exports** (except Next.js route files) | Named exports are grep-able, refactor-safe, and prevent silent rename bugs. |
| **Barrel files (`index.ts` re-exports)** | They break tree-shaking, create circular dependency traps, and make imports ambiguous. Import from the exact file. |
| **`any` type** | `unknown` + type narrowing or `as` cast at validated boundaries. `any` disables the compiler — the one tool catching bugs before runtime. |
| **`enum`** | Use `as const` objects or union string literals. Enums have surprising runtime behavior and don't play well with Zod. |
| **Relative imports across module boundaries** | Use `@/` path alias everywhere: `import { db } from "@/lib/db"`. Relative paths break when files move. |
| **Client-side data fetching for initial loads** | Server Components fetch at request time. No `useEffect` + loading spinner for data that's available on the server. SWR/React Query only for polling or optimistic updates. |
| **`fetch` to own API routes from server code** | Server actions and direct DB queries are faster and type-safe. API routes exist for external consumers (webhooks, mobile apps). |
| **Global state libraries (Redux, Zustand)** | Server Components eliminated most client state. For the rest, React Context + `useReducer` is sufficient. A SaaS app with SQLite does not need a client-side cache layer. |
| **`useEffect` for data fetching** | This is the pre-RSC pattern. Server Components fetch data. `useEffect` is for side effects (DOM manipulation, subscriptions), not data. |
| **Storing money as floats** | Store as integer cents. `price INTEGER NOT NULL` (2999 = $29.99). Floats cause rounding errors in billing — the one place you cannot afford them. |
| **`new Date()` in SQLite** | Use `strftime('%Y-%m-%dT%H:%M:%fZ', 'now')` in SQL. Store all timestamps as ISO-8601 TEXT in UTC. JavaScript Date objects lose timezone context. |
| **Wrapping every query in try-catch** | better-sqlite3 is synchronous. Errors mean bugs (bad SQL, schema mismatch). Let them crash in dev, catch at the boundary (error.tsx) in prod. |
| **`console.log` in production** | Use a structured logger (pino). `console.log` has no levels, no timestamps, no structured fields. It's for debugging, not observability. |
| **Environment variables without validation** | Validate all env vars at startup with Zod. Fail fast with a clear message, not halfway through a request with `undefined is not a function`. |

---

## Environment Variable Validation

```typescript
// src/config/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXTAUTH_SECRET: z.string().min(32),
  NEXTAUTH_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_"),
  SMTP_HOST: z.string().optional(),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
});

export const env = envSchema.parse(process.env);
```

Import `env` instead of using `process.env` directly. This gives autocomplete, type safety, and startup validation.

---

## Testing Strategy

- **Unit tests (Vitest):** Pure functions, Zod schemas, utility helpers. Fast, no DB.
- **Integration tests (Vitest):** Query functions against a test SQLite DB (in-memory or temp file). Test real SQL, not mocked queries.
- **E2E tests (Playwright):** Critical user flows — signup, create team, billing. Run against `pnpm build && pnpm start`.

**Rules:**
- Never mock the database. SQLite is fast enough to use a real instance in tests.
- Never mock `fetch` for internal calls. Test the actual server action or API route.
- Test files mirror source structure: `src/lib/db/queries/teams.ts` → `tests/unit/lib/db/queries/teams.test.ts`.
- Every server action has at least one integration test covering the happy path and one covering auth failure.

---

## Performance Defaults

- **`loading.tsx`** in every route group — instant shell while data loads.
- **`<Suspense>`** around slow data fetches within a page — don't block the whole page.
- **`next/image`** for all images. No raw `<img>` tags.
- **`next/font`** for fonts. No external font CDN requests.
- **`export const dynamic = "force-static"`** on pages that don't need request-time data (marketing, docs). Let Next.js cache them.
- **SQLite `EXPLAIN QUERY PLAN`** before adding indexes you're not sure about. Don't guess.

---

## Git Conventions

- **Branch naming:** `feat/short-description`, `fix/short-description`, `chore/short-description`.
- **Commit messages:** imperative mood, < 72 chars. `add team creation flow`, `fix slug validation`, `update auth session config`.
- **One concern per commit.** Migration + query function + server action + UI can be one commit if they're one feature. Don't split artificially, but don't bundle unrelated changes.
- **Never commit `.env.local` or `data/*.db`.** Both are in `.gitignore`. Verify before every commit.

---

## Dependency Policy

- **Add a dependency only when it saves > 100 lines of non-trivial code.** Small utilities (slugify, nanoid) are fine. Large frameworks for simple problems are not.
- **No `lodash`.** Modern JS covers it. Use native array methods.
- **No `moment` or `dayjs`.** Use `Intl.DateTimeFormat` or the lightweight `date-fns` (tree-shakeable).
- **Audit before adding:** check bundle size (bundlephobia), maintenance status, and whether it pulls in native dependencies. Native deps complicate deployment.
