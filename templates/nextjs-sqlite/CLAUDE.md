# CLAUDE.md — Next.js 15 + SQLite SaaS Template

> Production-ready guidelines and context for Claude Code when building on Next.js 15 App Router with SQLite (better-sqlite3 / Turso + Drizzle ORM).

---

## 1. Stack & Runtime Versions

| Tool / Layer | Version / Target | Choice Justification |
| :--- | :--- | :--- |
| **Framework** | Next.js 15 (App Router, React 19) | Server Actions, Streaming, Turbopack default |
| **Language** | TypeScript (Strict mode enabled) | End-to-end type safety |
| **Database Engine** | SQLite via `better-sqlite3` (Local / Node) or `@libsql/client` (Turso / Edge / Serverless) | Zero-latency embedded reads, easy local testing, simple replication |
| **ORM / Query Builder** | Drizzle ORM (`drizzle-orm` + `drizzle-kit`) | Zero runtime overhead, clean SQL-like TypeScript API, lightweight migrations |
| **Styling** | Tailwind CSS v4 | Co-located utility styles, zero runtime CSS-in-JS |
| **UI Primitives** | Radix UI / shadcn/ui patterns | Accessible primitives without heavy runtime bundles |
| **Validation** | Zod v3 | Schema validation on Server Actions and API boundaries |
| **Auth** | Auth.js (NextAuth v5) or Lucia pattern | Session cookies with SQLite adapter |

---

## 2. Project Folder Structure

Follow this strict directory organization:

```
├── src/
│   ├── app/                          # Next.js 15 App Router pages & route handlers
│   │   ├── (auth)/                   # Route group: login, register, forgot-password
│   │   ├── (dashboard)/              # Route group: authenticated SaaS workspace
│   │   │   ├── settings/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── api/                      # Webhooks and external API endpoints only
│   │   │   └── webhooks/stripe/route.ts
│   │   ├── layout.tsx                # Root layout
│   │   ├── page.tsx                  # Marketing / landing page
│   │   └── globals.css
│   ├── actions/                      # Server Actions (Mutations & form submissions)
│   │   ├── auth.ts
│   │   └── projects.ts
│   ├── components/                   # React components
│   │   ├── ui/                       # Atomic shadcn/ui components (button, dialog, input)
│   │   ├── layout/                   # Navbar, sidebar, footer
│   │   └── forms/                    # Reusable form components with validation
│   ├── db/                           # Database setup, schema, and migrations
│   │   ├── schema/                   # Modular schema definitions
│   │   │   ├── users.ts
│   │   │   ├── sessions.ts
│   │   │   └── index.ts
│   │   ├── migrations/               # Generated migration SQL files
│   │   ├── client.ts                 # Database connection singleton
│   │   └── seed.ts                   # Dev seeding script
│   ├── lib/                          # Pure business logic and utilities
│   │   ├── utils.ts                  # cn() and general helpers
│   │   ├── env.ts                    # Type-safe environment variables parser
│   │   └── auth.ts                   # Auth helpers and session extractors
│   └── types/                        # Shared TypeScript interfaces & types
├── drizzle.config.ts                 # Drizzle kit migration configuration
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 3. Essential Developer Commands

```bash
# Development
pnpm dev              # Start Turbopack dev server on localhost:3000
pnpm build            # Build production bundle
pnpm start            # Start production server
pnpm lint             # Run ESLint check
pnpm typecheck        # Run tsc --noEmit check

# Database & Migrations (Drizzle)
pnpm db:generate      # Generate SQL migration files from schema diffs
pnpm db:migrate       # Apply pending migrations to the SQLite database
pnpm db:push          # Fast schema push for rapid local prototyping
pnpm db:studio        # Launch Drizzle Studio Web GUI on localhost:4983
pnpm db:seed          # Run initial seed data script
```

---

## 4. SQL & SQLite Migration Rules

1. **Foreign Keys Must Be Explicitly Enabled**:
   SQLite disables foreign keys by default per connection. Always initialize SQLite connections with `PRAGMA foreign_keys = ON;` and `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for concurrency).
2. **Deterministic Primary Keys**:
   Use `text("id").primaryKey()` with `nanoid`, `uuidv7`, or `cuid2` generated application-side, or `integer("id").primaryKey({ autoIncrement: true })`.
   *Prefer text ID prefixes in multi-tenant SaaS* (e.g. `usr_123`, `org_456`, `proj_789`).
3. **Timestamps as ISO Strings or Integer Epoch**:
   Store timestamps as integer unix epochs (`timestamp: integer({ mode: "timestamp" })`) or ISO-8601 strings to ensure deterministic timezone comparison.
4. **Never Alter Migrations Retroactively**:
   Once a migration file in `src/db/migrations/` is committed, never edit it manually. Always generate a new incremental migration via `pnpm db:generate`.
5. **Collation for Case-Insensitive Lookups**:
   Use `COLLATE NOCASE` for email and username columns to avoid duplicated accounts with mixed cases.

---

## 5. Next.js 15 Component & Action Patterns

### Server vs. Client Components
- **Default to React Server Components (RSC)**: Fetch data directly in `page.tsx` or `layout.tsx` using server-side DB queries. No `useEffect` fetching!
- **Use Client Components (`"use client"`) only for**:
  - Interactivity (buttons with local state, modals, tabs).
  - Browser APIs (localStorage, clipboard, window events).
  - Form validation hooks (`react-hook-form`).

### Server Actions Pattern
Mutations must use Server Actions placed in `src/actions/`:
```typescript
"use server";

import { z } from "zod";
import { db } from "@/db/client";
import { projects } from "@/db/schema";
import { revalidatePath } from "next/cache";

const CreateProjectSchema = z.object({
  name: z.string().min(3).max(50),
  description: z.string().optional(),
});

export async function createProjectAction(formData: FormData) {
  const parsed = CreateProjectSchema.safeParse({
    name: formData.get("name"),
    description: formData.get("description"),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await db.insert(projects).values({
    name: parsed.data.name,
    description: parsed.data.description,
  });

  revalidatePath("/dashboard");
  return { success: true };
}
```

---

## 6. What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It | What To Do Instead |
| :--- | :--- | :--- |
| **No API routes (`/api/...`) for basic UI CRUD** | Next.js 15 Server Actions provide direct RPC, automatic revalidation, and zero client boilerplate. | Use Server Actions in `src/actions/`. Reserve `/api/` exclusively for external webhooks (e.g. Stripe, Resend). |
| **No Client-side DB or raw queries in client components** | Exposes database credentials and fails in browser execution contexts. | Keep queries in Server Components or Server Actions. |
| **No unchecked `any` or loose types** | Hides nullability bugs and breaks autocomplete. | Use Drizzle-inferred types: `type User = typeof users.$inferSelect;`. |
| **No raw string SQL interpolation** | Vulnerable to SQL injection. | Use Drizzle parameter binding or template tags (`sql\`SELECT * FROM users WHERE id = ${userId}\``). |
| **No heavy state management (Redux, MobX)** | Adds unnecessary bundle weight; Server Components handle state via URL and server revalidation. | Use URL search params (`nuqs`) or lightweight React context where necessary. |
| **No monolithic schema files** | Hard to maintain and leads to merge conflicts. | Keep schemas separated by domain in `src/db/schema/` and re-export via `index.ts`. |
