# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Paste this file as `CLAUDE.md` in the root of any greenfield
> Next.js + SQLite SaaS project. No modification needed — only fill in
> the 3 project-specific values in §0.
>
> Tested against: `create-next-app@15`, `drizzle-orm`, `better-sqlite3` /
> `@libsql/client` (Turso). See `README.md` in this folder for the
> greenfield test procedure.

## 0. Project facts (fill in once, 30 seconds)

```yaml
project_name: "TODO — e.g. acme-billing"
database: "sqlite" # local: better-sqlite3 file ./data/app.db | prod: Turso via libsql
auth: "TODO — e.g. Auth.js v5 (credentials + google)"
```

If these three lines are empty, ask for them first, then proceed.
Do not ask anything else — everything below is already decided.

---

## 1. Stack & versions (do not substitute)

| Layer     | Choice                                            | Why — the reason behind the rule                              |
|-----------|---------------------------------------------------|---------------------------------------------------------------|
| Framework | Next.js **15** App Router, React **19**, TS **strict** | App Router is the only supported pattern; Pages Router is dead. Strict TS catches null-tenant bugs at build time. |
| Language  | TypeScript `strict: true`, no `any`               | `any` hides multi-tenant leaks. Use `unknown` + Zod narrowing. |
| Styling   | Tailwind CSS v4, `cn()` from `lib/utils.ts`       | One styling system. No CSS modules, no styled-components — they fragment the design system. |
| DB        | SQLite — `better-sqlite3` locally, `@libsql/client` (Turso) in prod | Single file = zero-config local dev, instant prod via Turso replica. Postgres is overkill before $10k MRR. |
| ORM       | Drizzle ORM + Drizzle Kit                         | Prisma's engine + migration weight is unjustified for SQLite; raw SQL strings don't scale. Drizzle = typed SQL, zero magic. |
| Validation| Zod v3 for every Server Action / route input      | Never trust the client. Zod is the single validation gate.    |
| Auth      | Auth.js v5 (NextAuth)                             | Don't roll your own session cookies. Auth.js handles rotation, JWT + DB sessions correctly. |
| Data fetch| React Server Components + `fetch` / Drizzle directly | No React Query, no SWR, no Redux for server state — RSC already dedupes and caches. Client state only via `useState`/`zustand` when truly interactive. |

Engine: Node **20 LTS** (`lts/iron`), package manager **npm** (lockfile `package-lock.json` committed).

---

## 2. Dev commands (use exactly these)

```bash
npm run dev          # next dev — local app on :3000, reads .env.local
npm run build        # next build — must pass with zero TS/eslint errors
npm run start        # next start — prod preview
npm run lint         # next lint (eslint + no-unused-vars as errors)
npm run typecheck    # tsc --noEmit — run before every commit
npm run test         # vitest run — unit tests
npm run test:e2e     # playwright test — only for critical flows (signup → pay → dashboard)

npm run db:generate  # drizzle-kit generate — create SQL migration from schema change
npm run db:migrate   # drizzle-kit migrate — apply migrations to dev DB
npm run db:studio    # drizzle-kit studio — visual DB browser
npm run db:seed      # tsx ./db/seed.ts — idempotent seed (upserts only)
```

Env files (never commit `.env*.local`):

```bash
# .env.local (local dev)
DATABASE_URL="file:./data/app.db"
AUTH_SECRET="<openssl rand -base64 32>"

# .env.production (Turso)
DATABASE_URL="libsql://<db>-<org>.turso.io"
DATABASE_AUTH_TOKEN="<turso token>"
```

Rule: code reads config **only** via `lib/env.ts` (Zod-parsed). Never call `process.env.X` inline — reason: fail-fast on boot with a readable error instead of a `null` crash at 2 a.m.

---

## 3. Folder structure / project structure (create exactly this on greenfield)

```
app/
  (marketing)/page.tsx            # public landing — no auth, static
  (marketing)/pricing/page.tsx
  (app)/dashboard/page.tsx        # authenticated group — layout checks session
  (app)/dashboard/layout.tsx      # <AuthGuard> + <Sidebar> + tenant scope
  api/webhooks/stripe/route.ts    # ONLY webhook + edge-compat routes go in api/
  actions/                        # Server Actions, one file per domain
    billing.ts
    projects.ts
  layout.tsx                      # root layout: fonts, <Providers>, metadata
  globals.css                     # tailwind import only — no custom classes
components/
  ui/                             # shadcn-style primitives ONLY (Button, Dialog, Input…)
  features/billing/UpgradeButton.tsx  # feature components, colocated by domain
  layout/Sidebar.tsx
lib/
  db.ts                           # singleton Drizzle client (better-sqlite3 | libsql switch)
  env.ts                          # Zod-parsed env (single source of truth)
  auth.ts                         # Auth.js config
  utils.ts                        # cn() only — no business logic here
  validations/billing.ts          # Zod schemas, one file per domain (mirrors app/actions)
db/
  schema/                         # one file per table group: users.ts, projects.ts, billing.ts
    _root.ts                      # re-exports everything — single import point
  migrations/                     # Drizzle-generated SQL ONLY — never hand-edit applied ones
  seed.ts                         # idempotent upserts
tests/
  unit/validations.test.ts
  e2e/smoke.spec.ts
middleware.ts                     # auth redirect ONLY — no DB calls here (edge has no sqlite file)
```

Rules with reasons:

1. **Route groups `(marketing)` / `(app)` separate public from authed UI.** Reason: one `layout.tsx` guard per group beats sprinkling `if (!session) redirect()` in 20 pages.
2. **Mutations live in `app/actions/*.ts`, never in `api/` routes.** Reason: Server Actions give typed args + progressive enhancement for free; `api/` routes are for webhooks/cron that need raw `Request`.
3. **`components/ui` is dumb; `components/features` is smart.** Reason: primitives stay reusable; domain logic stays grep-able. Never import `db` into `components/ui`.
4. **`lib/` never imports from `app/` or `components/`.** Reason: dependency flows one way (`app → components → lib → db`). Circular imports = untestable code.
5. **`middleware.ts` does redirects only.** Reason: edge middleware cannot open a `better-sqlite3` file; any DB call there crashes prod.

---

## 4. Naming conventions (enforced in review)

| Thing | Convention | Example | Why |
|---|---|---|---|
| Files / dirs | `kebab-case` | `upgrade-button.tsx`, `api-keys/` | macOS (case-insensitive) + Linux (sensitive) diverge on `PascalCase` — kebab never collides. |
| Components | `PascalCase` export, file kebab | `export function UpgradeButton` in `upgrade-button.tsx` | File system ≠ JS symbol; keeps imports uniform. |
| Server Actions | `verbNoun` + `'use server'` top | `export async function createProject(input: CreateProjectInput)` | Reads like an RPC; grep for `create*` finds all writes. |
| DB tables | `snake_case` plural | `projects`, `api_keys` | Matches SQL convention; Drizzle `sqliteTable('api_keys', …)`. |
| DB columns | `snake_case`, `id` = `text` PK (nanoid/uuid), timestamps `created_at` / `updated_at` integer (unix ms) | `created_at INTEGER NOT NULL` | Text PKs merge cleanly across Turso replicas; integer timestamps sort and index without timezone hell. |
| Zod schemas | `NounSchema`, inferred `NounInput` | `export const CreateProjectSchema = z.object(…); export type CreateProjectInput = z.infer<…>` | One name for runtime + type — they can never drift. |
| Env vars | `SCREAMING_SNAKE`, validated in `lib/env.ts` | `DATABASE_URL` | Standard; validated once so the rest of the code trusts it. |
| Tests | `*.test.ts` (unit), `*.spec.ts` (e2e) | `validations.test.ts` | Vitest picks up `.test`, Playwright picks up `.spec` — no config overlap. |

---

## 5. SQL / migration conventions — database rules (hard rules — breakage = data loss)

1. **Schema changes ONLY via `db/schema/*.ts` + `npm run db:generate`.** Never write `CREATE TABLE` by hand, never edit `db/migrations/*.sql` after it has been applied anywhere. Reason: Drizzle Kit's journal (`_journal.json`) is the source of truth; hand edits desync it and brick `migrate`.
2. **SQLite DDL limits are real — follow the expansion/contraction pattern.** SQLite cannot `ALTER COLUMN` / `DROP COLUMN` cleanly. To rename/change: (a) `ADD COLUMN new`, (b) backfill in `seed.ts` or a one-off script, (c) deploy, (d) drop old column in a *later* migration. Reason: Turso replicas replay migrations; a single destructive rewrite locks the DB.
3. **Every table gets: `id TEXT PRIMARY KEY`, `created_at INTEGER NOT NULL`, and (if user-owned) `user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE`.** Reason: uniform PKs make generic helpers possible; missing `ON DELETE CASCADE` orphans billing rows.
4. **Multi-tenant rule: every query on a user-owned table MUST filter by `user_id` (or join through it).** Add a code-review checklist item for this. Reason: SQLite has no RLS — the app layer *is* the security boundary. One missing `where(eq(projects.userId, session.user.id))` = cross-tenant leak.
5. **Transactions for ≥2 writes: `await db.transaction(async (tx) => …)`.** Reason: `better-sqlite3` is synchronous under the hood; without an explicit transaction a crash between two writes leaves half an order.
6. **Migrations run at deploy/startup (`db:migrate`), never lazily per-request.** Reason: concurrent first-requests race `CREATE TABLE IF NOT EXISTS` and corrupt the journal on a fresh Turso branch.
7. **Seeds are idempotent upserts (`onConflictDoNothing` / `onConflictDoUpdate`).** `npm run db:seed` must be safe to run 10×. Reason: CI and preview branches re-seed constantly.
8. **No `SELECT *`. List columns explicitly.** Reason: schema additions silently leak new PII (e.g. `stripe_customer_id`) into API responses.

Minimal schema example (copy-paste starter):

```ts
// db/schema/projects.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const projects = sqliteTable("projects", {
  id: text("id").primaryKey(),              // nanoid in action layer
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
```

Client singleton pattern (do not deviate):

```ts
// lib/db.ts
import { drizzle as drizzleSqlite } from "drizzle-orm/better-sqlite3";
import { drizzle as drizzleLibsql } from "drizzle-orm/libsql";
import Database from "better-sqlite3";
import { createClient } from "@libsql/client";
import { env } from "./env";
import * as schema from "@/db/schema/_root";

export const db =
  env.DATABASE_URL.startsWith("libsql://")
    ? drizzleLibsql(createClient({ url: env.DATABASE_URL, authToken: env.DATABASE_AUTH_TOKEN }), { schema })
    : drizzleSqlite(new Database(env.DATABASE_URL.replace("file:", "")), { schema });
// Reason: one import (`@/lib/db`) works in dev AND prod. Branching at call sites duplicates the bug surface.
```

---

## 6. Component patterns & data patterns (follow these)

**Server Component by default.** Add `'use client'` only when you need `useState`/`useEffect`/browser APIs. Reason: server components keep the API key and DB handle server-side and ship zero JS.

```tsx
// ✅ Server Component fetches directly — no useEffect, no loading waterfall
import { db } from "@/lib/db";
import { projects } from "@/db/schema/_root";
import { eq } from "drizzle-orm";
import { auth } from "@/lib/auth";

export async function ProjectList() {
  const session = await auth();
  if (!session?.user) return null; // layout already guards; belt + suspenders
  const rows = await db.select().from(projects).where(eq(projects.userId, session.user.id));
  return <ul>{rows.map((p) => <li key={p.id}>{p.name}</li>)}</ul>;
}
```

**Mutations via Server Actions + Zod + revalidate.** One file per domain in `app/actions/`.

```ts
// app/actions/projects.ts
"use server";
import { z } from "zod";
import { nanoid } from "nanoid";
import { revalidatePath } from "next/cache";
import { db } from "@/lib/db";
import { projects } from "@/db/schema/_root";
import { auth } from "@/lib/auth";
import { CreateProjectSchema } from "@/lib/validations/projects";

export async function createProject(raw: z.infer<typeof CreateProjectSchema>) {
  const session = await auth();
  if (!session?.user) throw new Error("UNAUTHORIZED"); // never trust client session flag
  const input = CreateProjectSchema.parse(raw);        // validate AFTER auth, BEFORE db
  const now = Date.now();
  await db.insert(projects).values({ id: nanoid(), userId: session.user.id, name: input.name, createdAt: now, updatedAt: now });
  revalidatePath("/dashboard"); // Reason: explicit revalidation beats router.refresh() spaghetti
}
```

**Forms:** uncontrolled + `useActionState` (React 19) or plain `<form action={createProject}>`. No `react-hook-form` for simple CRUD. Reason: native form actions give progressive enhancement; RHF is justified only for 10+-field wizards.

**Errors:** Actions throw `Error("UNAUTHORIZED" | "FORBIDDEN" | "NOT_FOUND")`; `error.tsx` boundaries map them to status copy. Never return `{ error }` unions from actions — reason: thrown errors trigger the nearest `error.tsx` automatically; union returns force every caller to branch.

**Styling:** `cn("px-4 py-2", condition && "bg-black")`; responsive mobile-first (`md:` up). No inline `style={{}}` except measured values (e.g. canvas). Reason: Tailwind classes are grep-able; inline styles bypass the design system.

---

## 7. What we don't do — anti-patterns to avoid (and why)

| ❌ Don't | ✅ Do instead | Why |
|---|---|---|
| Prisma + SQLite in prod | Drizzle + better-sqlite3 / Turso | Prisma needs a query engine binary; it breaks on edge/serverless and triples `npm install` time for zero gain at SaaS-MVP scale. |
| `api/` route per CRUD op | Server Actions in `app/actions/` | Each `api/` route re-invents auth, validation, serialization. Actions inherit cookies + session typing. |
| `useEffect` data fetching | Async Server Component | Effects waterfall, flash spinners, and expose DB shapes to the client bundle. |
| ORM-less raw SQL strings | Drizzle query builder | Raw strings lose type-checking on renames; Drizzle compiles to the same SQL with rename safety. |
| `process.env` sprinkled everywhere | `lib/env.ts` Zod gate | A typo'd env name becomes a runtime `undefined` three files deep instead of a boot-time error. |
| Committed `.db` / `.sqlite` files | `data/*.db` in `.gitignore`, seed via `db:seed` | Binary diffs pollute PRs and leak customer rows into git history forever. |
| `DATABASE_URL` pointing at a shared dev DB | Local file per dev (`./data/app.db`) | SQLite is a file — sharing one file over the network corrupts it. Each dev owns their file. |
| Client components importing `db` | Pass data down as props from a Server Component | `better-sqlite3` is Node-only; importing it client-side bloats/breaks the bundle and leaks the DB path. |
| `any`, `@ts-ignore`, `as any` | `unknown` + Zod `.parse`, or precise `as` with comment | Silenced types are how tenant-id bugs ship. CI `typecheck` fails on `any`. |
| Barrel `index.ts` re-exports in `components/` | Direct deep imports (`@/components/features/billing/upgrade-button`) | Barrels force the bundler to evaluate the whole folder and create phantom cycles. Only `db/schema/_root.ts` may barrel (Drizzle needs one schema object). |
| `next/image` with external URLs + no loader | Local `/public` images, or configured `remotePatterns` | Unconfigured remote images throw at runtime in prod only — the worst kind of bug. |

---

## 8. Definition of done (check before every PR)

- [ ] `npm run typecheck` + `npm run lint` + `npm run build` green, zero warnings
- [ ] New/changed tables have a Drizzle migration (`db/migrate` applies cleanly on a fresh `app.db`)
- [ ] Every new query on user data filters by `user_id` (search diff for `.from(` without a `.where(`)
- [ ] No `'use client'` added without a browser-API justification in the PR description
- [ ] No `.db` file, no `.env*.local`, no secret in the diff (`git status --porcelain` shows only code)
- [ ] E2E smoke (`signup → create project → delete`) passes if auth or billing touched

*Keep this file under 500 lines. If a rule needs more than 3 sentences of explanation, it belongs in a linked ADR, not here.*
