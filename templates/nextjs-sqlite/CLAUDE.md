# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Drop this file into the root of a greenfield Next.js 15 App Router + SQLite project. Claude Code will pick it up automatically.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components + streaming by default |
| Runtime | Node.js | 22 LTS | Required by Next.js 15 |
| Language | TypeScript | 5.x | Strict mode — no `any` |
| Database | better-sqlite3 | 11.x | Sync API = zero connection pooling bugs in serverless |
| ORM | Drizzle ORM | 0.x | Lightweight, SQL-like, generates migrations |
| Auth | NextAuth.js v5 | 5.x-beta | Built for App Router |
| Styling | Tailwind CSS | 4.x | Utility-first, zero runtime |
| Validation | Zod | 3.x | Schema = types, single source of truth |
| Testing | Vitest + Testing Library | latest | Fast, ESM-native, works with Server Components |

**No Prisma.** Prisma's Rust engine adds cold-start latency that kills serverless SQLite.

---

## Folder Structure

```
src/
  app/                    # Next.js App Router
    (auth)/               # Auth route group (login, signup)
      login/page.tsx
      signup/page.tsx
    (dashboard)/          # Protected route group
      dashboard/page.tsx
      settings/page.tsx
    api/                  # Route handlers
      auth/[...nextauth]/route.ts
      webhooks/stripe/route.ts
    layout.tsx            # Root layout
    page.tsx              # Landing page
  components/
    ui/                   # Primitive components (Button, Input, Card)
    forms/                # Form components (LoginForm, SettingsForm)
    layouts/              # Layout components (Sidebar, Header)
  db/
    schema.ts             # Drizzle schema definitions
    migrations/           # Generated SQL migrations
    index.ts              # Database connection singleton
    seed.ts               # Dev seed script
  lib/
    auth.ts               # NextAuth config + helpers
    stripe.ts             # Stripe client + helpers
    validations.ts        # Shared Zod schemas
  actions/                # Server Actions
    auth.ts
    settings.ts
  middleware.ts           # Next.js middleware (auth checks)
drizzle.config.ts         # Drizzle Kit config
.env.local                # Secrets (never commit)
```

**Rule:** One concern per file. A component file exports exactly one component (plus its props type).

---

## Dev Commands

```bash
# Start dev server
pnpm dev

# Run database migrations
pnpm db:migrate          # → drizzle-kit push

# Generate a new migration after schema change
pnpm db:generate         # → drizzle-kit generate

# Open Drizzle Studio (visual DB browser)
pnpm db:studio           # → drizzle-kit studio

# Seed database with test data
pnpm db:seed             # → tsx src/db/seed.ts

# Run tests
pnpm test                # → vitest
pnpm test:ui             # → vitest --ui

# Type check
pnpm typecheck           # → tsc --noEmit

# Lint
pnpm lint                # → next lint
```

**All commands use `pnpm`.** No `npm` or `yarn` in this project.

---

## SQL / Migration Conventions

1. **Schema is source of truth.** Edit `src/db/schema.ts`, then run `pnpm db:generate`. Never hand-edit migration SQL.
2. **Column naming:** `snake_case` in DB, `camelCase` in TypeScript. Drizzle maps between them with `cz({ name: "created_at" })`.
3. **Every table has:**
   - `id` — text primary key (use `nanoid` or `cuid2`), never auto-increment integer
   - `created_at` — integer, Unix timestamp (not ISO string — SQLite has no native datetime)
   - `updated_at` — integer, Unix timestamp, updated via Drizzle `$onUpdate`
4. **Soft deletes only.** Add `deleted_at integer` column. Never `DELETE FROM` in production code.
5. **Boolean fields:** Store as `integer` (0/1). SQLite has no native boolean type.
6. **JSON fields:** Store as `text`, parse with `JSON.parse()` in the getter. Use Zod to validate on read.
7. **Foreign keys:** Always `references(() => table.id)` with `onDelete: "cascade"` unless there's a business reason to restrict.

```typescript
// Example schema definition
export const users = sqliteTable("users", {
  id: text("id").primaryKey(),           // cuid2
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  plan: text("plan", { enum: ["free", "pro", "enterprise"] }).default("free"),
  createdAt: integer("created_at").notNull().$default(() => Date.now()),
  updatedAt: integer("updated_at").notNull().$default(() => Date.now()).$onUpdate(() => Date.now()),
  deletedAt: integer("deleted_at"),      // soft delete
});
```

---

## Component Patterns

### Server Components (default)
Every page and layout is a Server Component unless it needs interactivity.

```tsx
// app/(dashboard)/dashboard/page.tsx — Server Component
import { getUser } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const user = await getUser();
  if (!user) redirect("/login");
  return <DashboardView user={user} />;
}
```

### Client Components (opt-in)
Add `"use client"` only when the component uses:
- Event handlers (`onClick`, `onChange`)
- React hooks (`useState`, `useEffect`)
- Browser APIs (`localStorage`, `window`)

```tsx
// components/ui/counter.tsx — Client Component
"use client";
import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Server Actions
All mutations go through Server Actions. Never call `fetch('/api/...')` from a client component for data writes.

```tsx
// actions/settings.ts
"use server";
import { db } from "@/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";

export async function updateName(formData: FormData) {
  const name = formData.get("name") as string;
  // Always validate with Zod before writing
  const parsed = nameSchema.parse({ name });
  await db.update(users).set({ name: parsed.name }).where(eq(users.id, userId));
  revalidatePath("/settings");
}
```

### Forms
Use `react-hook-form` + `zodResolver` on the client. Schema is shared with server.

```tsx
// components/forms/settings-form.tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolver/zod";
import { nameSchema } from "@/lib/validations";

export function SettingsForm() {
  const { register, handleSubmit } = useForm({ resolver: zodResolver(nameSchema) });
  return (
    <form action={updateName}>
      <input {...register("name")} />
      <button type="submit">Save</button>
    </form>
  );
}
```

---

## What We Don't Do (and Why)

| Don't | Why |
|-------|-----|
| No `getServerSideProps` or Pages Router | App Router is the standard. Mixing = confusion |
| No Prisma | Rust engine = slow cold starts with SQLite. Drizzle is 10x lighter |
| No `any` type | Strict TypeScript catches bugs at compile time |
| No `DELETE FROM` in production | Soft deletes only. Data is asset, not liability |
| No raw SQL strings | Use Drizzle query builder. If you need raw, put it in `db/raw.ts` with a comment explaining why |
| No client-side data fetching for mutations | Use Server Actions. No `fetch('/api/...')` for writes |
| No `useEffect` for data fetching | Use Server Components or `use()` hook. Effects are for side effects, not data |
| No environment variables without Zod validation | Parse `process.env` with Zod at app startup. Fail fast on missing vars |
| No monorepo tooling (Turborepo, Nx) | Single-package app until team size justifies the complexity |
| No auto-increment integer IDs | Cuid2/nanoid are globally unique, URL-safe, and don't leak record counts |
| No ISO date strings in SQLite | SQLite has no native datetime type. Store as Unix timestamp integer |

---

## Naming Conventions

- **Files:** `kebab-case.tsx` for components, `kebab-case.ts` for utilities
- **Directories:** `kebab-case/`
- **Components:** `PascalCase` exported as named export (`export function Button()`)
- **Server Actions files:** `kebab-case.ts` in `actions/`
- **DB schema files:** one table per export in `schema.ts`
- **CSS classes:** Tailwind utilities only, no custom CSS files unless absolutely necessary
- **Environment variables:** `UPPER_SNAKE_CASE`, prefixed by service (`STRIPE_SECRET_KEY`, `AUTH_SECRET`)

---

## Error Handling

- **Server Actions:** Return `{ error: string } | { data: T }`. Never throw to the client.
- **API Routes:** Return `{ error: { code: string, message: string } }` with appropriate HTTP status.
- **Database errors:** Catch with try/catch, return user-friendly message. Never expose SQL errors to the client.
- **Validation errors:** Zod `flattenErrors()` for form field mapping.

---

## Security

- Every route in `(dashboard)/` must check auth via `middleware.ts`
- API webhooks verify signatures (Stripe, GitHub, etc.)
- CSRF protection is handled by Next.js Server Actions (same-origin by default)
- Rate limiting via `upstash/ratelimit` on auth endpoints
- Never store secrets in client components. All keys stay in Server Components or Route Handlers.
