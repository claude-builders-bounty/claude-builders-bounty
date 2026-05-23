# CLAUDE.md — Next.js 15 + SQLite SaaS Stack

> Opinionated, production-ready. Every rule has a reason.
> Drop this into any greenfield Next.js + SQLite SaaS project.

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | RSC, streaming, server actions — no need for a separate API layer |
| Language | TypeScript | 5.7+ | Strict mode on. Any is a code smell. |
| Database | Turso (libSQL) | latest | Edge-ready SQLite. Better than better-sqlite3 for serverless deploys. |
| ORM | Drizzle | 0.40+ | Type-safe SQL without the Prisma bloat. Migrations are just SQL files. |
| Auth | NextAuth v5 | 5.x | Auth.js v5. JWT sessions by default — no DB session table needed. |
| Styling | Tailwind CSS | 4.x | Utility-first. No CSS modules, no styled-components. Shadcn/ui for components. |
| Validation | Zod | 3.x | Same schemas for client forms AND server actions. One source of truth. |
| Package Manager | pnpm | 9.x | Fast, strict, disk-efficient. No npm, no yarn. |

## Folder Structure

```
src/
├── app/                    # App Router — routes live here
│   ├── (auth)/             # Auth group layout (login, register, verify)
│   │   ├── login/page.tsx
│   │   └── layout.tsx      # Auth layout — no navbar, centered card
│   ├── (dashboard)/        # Dashboard group layout (authenticated)
│   │   ├── layout.tsx      # Dashboard shell — sidebar + topbar
│   │   ├── page.tsx        # /dashboard → redirect to default view
│   │   └── settings/       # /dashboard/settings
│   ├── api/                # Route handlers (webhooks, external APIs)
│   └── layout.tsx          # Root layout — providers, fonts, metadata
├── components/
│   ├── ui/                 # shadcn/ui primitives (button, input, dialog…)
│   ├── forms/              # Form components — always RHF + Zod
│   └── features/           # Feature-specific components
│       ├── billing/
│       ├── teams/
│       └── settings/
├── db/
│   ├── schema/             # Drizzle schema files — one file per domain
│   │   ├── users.ts
│   │   ├── teams.ts
│   │   └── billing.ts
│   ├── migrations/         # Auto-generated SQL migrations. Never edit manually.
│   ├── index.ts            # Exports { db } — Turso client singleton
│   └── seed.ts             # Dev seed data
├── lib/
│   ├── auth.ts             # NextAuth config — callbacks, providers
│   ├── auth-client.ts      # Client-side auth helpers (useSession wrapper)
│   ├── db.ts               # Re-exports db for convenience
│   ├── email.ts            # Resend or Postmark mailer
│   ├── stripe.ts           # Stripe SDK singleton
│   └── utils.ts            # cn(), formatDate(), slugify() — no business logic
├── hooks/                  # Shared hooks — useCurrentUser, useTeam, useMediaQuery
├── server/                 # Server-only logic (never imports "use client")
│   ├── mutations/          # Server actions — one file per domain
│   │   ├── users.ts
│   │   ├── teams.ts
│   │   └── billing.ts
│   └── queries/            # Data fetching functions — typed, cached
├── types/                  # Shared TypeScript types
├── middleware.ts            # Next.js middleware — auth guard, redirects
└── env.ts                  # Typed env vars (t3-env pattern)
```

## Dev Commands

```bash
pnpm dev          # Start dev server
pnpm build        # Production build
pnpm start        # Start production server
pnpm lint         # ESLint + TypeScript check
pnpm format       # Prettier write
pnpm db:generate  # Drizzle: generate migration from schema changes
pnpm db:migrate   # Drizzle: apply migrations
pnpm db:push      # Drizzle: push schema directly (dev only, never in prod)
pnpm db:studio    # Drizzle Studio — visual DB browser
pnpm db:seed      # Seed development data
pnpm test         # Vitest (unit + integration)
pnpm test:e2e     # Playwright e2e
```

## SQL / Migration Conventions

### Rules
- **Never edit migration files.** Generate with `pnpm db:generate`, apply with `pnpm db:migrate`.
- **One migration per schema change.** Don't batch unrelated changes.
- **Always nullable by default.** Unless you have a hard business reason for NOT NULL, keep it nullable. Easier to relax later.
- **Use TEXT for IDs.** CUID2 strings (`tz4a98xxat96iws9zmbrgj3a`). No auto-increment integers. No UUIDs.
- **Timestamps are ISO 8601 strings.** No Date objects. Store as TEXT, parse at the edge.
- **Soft deletes with `deleted_at`.** Never `DELETE FROM`. Always `UPDATE SET deleted_at = now()`.

### Schema Example

```typescript
// db/schema/users.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name"),
  avatarUrl: text("avatar_url"),
  createdAt: text("created_at").notNull().$defaultFn(() => new Date().toISOString()),
  updatedAt: text("updated_at").notNull().$defaultFn(() => new Date().toISOString()),
  deletedAt: text("deleted_at"),
});
```

## Component Patterns

### Server Components by Default
Everything is a Server Component unless it needs interactivity.
```typescript
// app/(dashboard)/settings/page.tsx
import { getUserSettings } from "@/server/queries/settings";
import { SettingsForm } from "@/components/features/settings/SettingsForm";

export default async function SettingsPage() {
  const settings = await getUserSettings(); // Direct DB query, no fetch()
  return <SettingsForm defaults={settings} />;
}
```

### Client Boundaries
Keep `"use client"` as low in the tree as possible.
```typescript
// components/features/settings/SettingsForm.tsx
"use client";
// Only this leaf component is client-side.
```

### Forms: RHF + Zod + Server Actions
```typescript
const schema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
});
type FormData = z.infer<typeof schema>;

export function SettingsForm({ defaults }: { defaults: FormData }) {
  const form = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: defaults });
  const [pending, setPending] = useState(false);

  async function onSubmit(data: FormData) {
    setPending(true);
    const result = await updateSettings(data); // Server action
    if (result.error) form.setError("root", { message: result.error });
    setPending(false);
  }
  // ...
}
```

### Data Fetching
- Server Components: call query functions directly (no API routes).
- Client Components: use server actions to trigger mutations, pass data as props.
- No React Query, no SWR, no tRPC. Server Components ARE your data layer.

## What We DON'T Do (And Why)

| Anti-pattern | Why we avoid it |
|-------------|-----------------|
| API routes for internal data | App Router lets you query DB directly in Server Components. No REST boilerplate. |
| `any` types | Strict TypeScript catches bugs at compile time. If you need `any`, fix the type. |
| `useEffect` for data fetching | Server Components handle initial data. Server actions handle mutations. |
| `SELECT *` | Always select explicit columns. Prevents accidental data leaks. |
| Bare `console.log` | Use structured logging (pino or similar). Logs go to stdout, parsed by your provider. |
| Environment variables in client code | Only `NEXT_PUBLIC_*` goes to the client. All others are server-only. |
| Prisma | Heavy, slow cold starts, opaque migrations. Drizzle gives you SQL control. |
| ORM-level cascading deletes | Handle cascades in application code. Explicit > implicit for data integrity. |
| `export default` for anything except pages | Named exports make refactoring safe and IDE autocomplete accurate. |
| Inline SQL in server components | All DB access goes through `server/queries` or `server/mutations`. Keeps data layer clean. |

## AI Assistant Instructions

When generating code for this project:
1. **Server actions go in `server/mutations/`** — never inline them in components.
2. **All DB queries use Drizzle** — no raw SQL strings in application code.
3. **Forms use `react-hook-form` + Zod** — no manual form state.
4. **Errors are returned, not thrown** — server actions return `{ error?: string, data?: T }`.
5. **Optimistic UI with `useTransition`** — show pending state, not loading spinners.
