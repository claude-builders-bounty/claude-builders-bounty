# CLAUDE.md — Next.js 15 + SQLite SaaS Blueprint 🏗️

> **Project Mission**: Lean, lightning-fast B2B/B2C SaaS built with Next.js 15 (App Router), TypeScript, SQLite (via Drizzle ORM + better-sqlite3 / Turso), and Tailwind CSS.
> **Design Philosophy**: Zero-bloat, server-first, type-safe end-to-end, edge-ready, single-command migrations.

---

## 🛠️ Stack & Verified Versions

- **Framework**: Next.js 15.x (`app` router only, React 19 Server Components)
- **Language**: TypeScript 5.x (Strict mode, `noImplicitAny: true`, `@/*` path alias)
- **Database**: SQLite via `better-sqlite3` (local dev) / `libsql` / `@libsql/client` (Turso production)
- **ORM & Migrations**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Styling**: Tailwind CSS v4 / v3.4 + Radix UI primitives
- **Auth**: Lucía Auth / NextAuth / Iron-session with SQLite session adapter
- **Validation**: Zod 3.x (API requests & Server Action payloads)
- **Package Manager**: `pnpm` (default) or `npm`

---

## 📁 Folder Structure & Organization

```
├── app/                      # Next.js App Router
│   ├── (auth)/               # Route group: login, register, reset-password
│   ├── (dashboard)/          # Route group: authenticated app layouts
│   │   ├── dashboard/page.tsx
│   │   └── settings/page.tsx
│   ├── api/                  # Route handlers (webhooks & public REST only)
│   ├── layout.tsx            # Root layout with font optimization & theme
│   └── page.tsx              # Public landing page
├── components/               # Reusable UI components
│   ├── ui/                   # Primitive design system (buttons, dialogs, inputs)
│   └── forms/                # Compound form components with Server Actions
├── db/                       # Database layer
│   ├── schema/               # Drizzle schema definitions (one file per domain)
│   │   ├── users.ts
│   │   ├── subscriptions.ts
│   │   └── index.ts          # Consolidated schema export
│   ├── migrations/           # Drizzle generated SQL migrations
│   ├── client.ts             # SQLite client singleton (WAL mode enabled)
│   └── migrate.ts            # Migration runner script
├── lib/                      # Shared business logic & utilities
│   ├── auth/                 # Session validation, cookie handling, password hashing
│   ├── payments/             # Stripe / LemonSqueezy webhook handlers
│   └── utils.ts              # cn(), date formatting, currency helpers
├── actions/                  # Server Actions (colocated by feature)
│   ├── auth.actions.ts
│   └── billing.actions.ts
└── types/                    # Global ambient types & Drizzle inferred types
```

---

## ⚡ Dev Commands & Workflow

```bash
# Development
pnpm dev                      # Starts Next.js dev server on http://localhost:3000
pnpm build                    # Runs typecheck + Next.js production build
pnpm start                    # Starts production standalone server

# Database & Migrations
pnpm db:generate              # Generates SQL migrations from db/schema/*.ts
pnpm db:migrate               # Applies pending migrations to SQLite database
pnpm db:studio                # Opens Drizzle Studio GUI for visual database inspection
pnpm db:seed                  # Seeds demo data into dev database

# Quality Assurance
pnpm typecheck                # tsc --noEmit
pnpm lint                     # eslint --max-warnings 0
pnpm test                     # vitest run (unit & integration tests)
```

---

## 📜 SQL & Migration Conventions

1. **WAL Mode is Mandatory**: Always initialize SQLite with `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL;` to allow high-concurrency reads alongside writes.
2. **Foreign Key Enforcement**: SQLite does not enforce foreign keys by default. Always execute `PRAGMA foreign_keys = ON;` on every database connection.
3. **Explicit Primary Keys**: Use `text("id").primaryKey().$defaultFn(() => createId())` (CUID2 / UUIDv7) for all entity IDs. Avoid raw auto-incrementing integers for public IDs.
4. **Timestamps**: All tables must include:
   ```ts
   createdAt: integer("created_at", { mode: "timestamp" }).notNull().default(sql`(strftime('%s', 'now'))`),
   updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().default(sql`(strftime('%s', 'now'))`)
   ```
5. **No Ad-Hoc DB Queries in Client Components**: All database operations MUST live in Server Components or Server Actions inside `/actions` or `/db/queries`.

---

## 🧩 Component & Server Action Patterns

### 1. Server Component by Default
All components in `app/` are Server Components unless `use client` is strictly required for event listeners or browser state.

### 2. Type-Safe Server Actions with Zod
```ts
// actions/project.actions.ts
"use server";
import { z } from "zod";
import { db } from "@/db/client";
import { projects } from "@/db/schema";
import { verifyAuthSession } from "@/lib/auth";

const CreateProjectSchema = z.object({
  title: z.string().min(3).max(100),
  description: z.string().optional()
});

export async function createProjectAction(formData: FormData) {
  const session = await verifyAuthSession();
  if (!session) return { success: false, error: "Unauthorized" };

  const parsed = CreateProjectSchema.safeParse({
    title: formData.get("title"),
    description: formData.get("description")
  });
  if (!parsed.success) return { success: false, errors: parsed.error.flatten() };

  const [project] = await db.insert(projects).values({
    ...parsed.data,
    userId: session.user.id
  }).returning();

  return { success: true, data: project };
}
```

---

## 🚫 What We DON'T Do (And Why)

1. **NO Heavy Client State Libraries (Redux, MobX)**:
   - *Why*: Next.js 15 Server Components and URL search params handle 95% of state. Use lightweight `zustand` or React Context only if client-side UI state is truly complex.
2. **NO Direct Prisma ORM on SQLite Edge**:
   - *Why*: Drizzle generates zero-overhead, human-readable SQL and compiles directly to edge-compatible WASM / native C bindings, beating Prisma binary cold-starts.
3. **NO Unvalidated API Routes**:
   - *Why*: Every single API route and Server Action must parse payloads with Zod before touching the database to prevent injection and corruption.
4. **NO Raw `fetch()` without Next.js Cache Tags**:
   - *Why*: Use `revalidateTag()` and `revalidatePath()` for granular cache purging instead of full-page refetches.
5. **NO Storing Passwords in Plaintext or MD5**:
   - *Why*: Use `bcrypt` or `@node-rs/argon2` with appropriate salt rounds.
