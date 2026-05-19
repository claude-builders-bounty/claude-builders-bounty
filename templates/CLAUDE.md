# CLAUDE.md

> This file provides context to Claude Code about this project.
> It is opinionated by design — every rule exists for a reason learned in production.

## Stack & Versions

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | ^15.0 |
| Language | TypeScript | ^5.5 |
| Database | SQLite (better-sqlite3) | ^11.0 |
| ORM | Drizzle ORM | ^0.36 |
| Auth | next-auth v5 (Auth.js) | ^5.0 |
| Styling | Tailwind CSS | ^3.4 |
| Validation | Zod | ^3.23 |
| Payments | Stripe | ^17.0 |
| Hosting | Vercel | — |

## Folder Structure

```
src/
├── app/                  # Next.js App Router — file-based routing
│   ├── (auth)/           # Route group: auth pages (login, register)
│   ├── (dashboard)/      # Route group: authenticated dashboard
│   │   ├── layout.tsx    # Dashboard shell (sidebar, nav)
│   │   └── settings/     # Nested route example
│   ├── api/              # API route handlers
│   │   └── stripe/       # Stripe webhook (raw body, no parser)
│   └── layout.tsx        # Root layout (fonts, metadata, providers)
├── components/
│   ├── ui/               # shadcn/ui primitives (Button, Input, Dialog)
│   └── features/         # Feature-specific composed components
├── lib/
│   ├── db/               # Database layer
│   │   ├── schema.ts     # Drizzle schema definitions
│   │   ├── migrations/   # Auto-generated SQL migrations
│   │   └── index.ts      # db singleton export
│   ├── auth.ts           # next-auth config
│   ├── stripe.ts         # Stripe client (server-only)
│   └── utils.ts          # cn(), formatCurrency(), etc.
├── hooks/                # Client-side React hooks
├── actions/              # Server Actions (use server)
└── types/                # Shared TypeScript types
```

**Why:** Route groups `(auth)` and `(dashboard)` keep layouts clean without affecting URLs. Server Actions go in `actions/` not `app/` to keep route files thin. DB layer in `lib/db/` is a single source of truth — never import drizzle directly elsewhere.

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files (components) | PascalCase | `UserAvatar.tsx` |
| Files (utilities) | camelCase | `formatDate.ts` |
| Server Actions | `action` + verb + noun | `createTeamAction.ts` |
| Database tables | snake_case, plural | `user_subscriptions` |
| DB columns | snake_case | `created_at`, `stripe_customer_id` |
| Zod schemas | camelCase + `Schema` | `createTeamSchema` |
| API routes | kebab-case folders | `api/teams/[teamId]/` |

**Why:** PascalCase for components matches React convention. snake_case for DB avoids quoting in SQL. Server Actions named with `Action` suffix so importing `createTeam` (the service) vs `createTeamAction` (the server action) is unambiguous.

## Database — SQLite Conventions

### Schema Design

- **Always use INTEGER for booleans**: SQLite has no native boolean. Map via Drizzle: `integer("is_active", { mode: "boolean" })`.
- **Always use TEXT for timestamps**: Store as ISO 8601 strings. Drizzle maps to JS Date automatically.
- **Always use TEXT for enums**: SQLite has no enum type. Validate at the application layer with Zod.
- **No foreign keys by default**: SQLite requires `PRAGMA foreign_keys = ON` per connection. Enable it in `lib/db/index.ts` on every connection.

```typescript
// lib/db/index.ts — THE pattern
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";

const sqlite = new Database(process.env.DATABASE_URL || "data.db");
sqlite.pragma("journal_mode = WAL");      // Better concurrent reads
sqlite.pragma("foreign_keys = ON");       // Required for FK enforcement
sqlite.pragma("busy_timeout = 5000");     // Wait up to 5s on lock

export const db = drizzle(sqlite);
export { sqlite }; // Only export for migrations — never use raw
```

**Why:** WAL mode allows concurrent readers. `foreign_keys = ON` is OFF by default in SQLite — forgetting this is the #1 production bug. `busy_timeout` prevents "database is locked" errors under load.

### Migrations

- **Run `drizzle-kit generate` after every schema change.**
- **Commit migration SQL files** — they are the source of truth.
- **Never edit migration files manually** — regenerate if wrong.
- **Apply in CI**: `drizzle-kit migrate` runs before deploy.
- **Rollback strategy**: Write an inverse migration, don't try to reverse-engineer.

### Query Rules

- **All DB queries go through `db` from `lib/db/`** — never create a second connection.
- **Use Drizzle query builders** — avoid raw SQL except for migrations.
- **Always `.get()` for single rows, `.all()` for lists** — never iterate a single-row result.
- **Transactions**: wrap in `db.transaction()`, keep them short, never await inside.

```typescript
// ✅ Good — single query, typed result
const user = db.select().from(users).where(eq(users.id, userId)).get();

// ❌ Bad — raw SQL for routine queries
const user = sqlite.prepare("SELECT * FROM users WHERE id = ?").get(userId);
```

## Component Patterns

### Server Components by Default

Every component starts as a Server Component. Only add `"use client"` when you need:
- `useState` / `useEffect` / `useReducer`
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`localStorage`, `window`, `navigator`)
- Custom hooks that use any of the above

```typescript
// ✅ Server Component — no 'use client', can be async
export async function TeamList() {
  const teams = await db.select().from(teams).all();
  return <ul>{teams.map(t => <TeamCard key={t.id} team={t} />)}</ul>;
}

// ✅ Client Component — 'use client', cannot be async
"use client";
export function TeamForm({ action }: { action: (fd: FormData) => Promise<void> }) {
  return <form action={action}>...</form>;
}
```

### Data Fetching

- **Fetch data in Server Components**, not in client components with `useEffect`.
- **Pass data as props** to client components — never fetch from the client.
- **Use Server Actions for mutations** — forms call `action={serverAction}`, not `onSubmit={fetch(...)}`.
- **Cache deliberately**: `unstable_cache` for expensive queries, `revalidatePath` after mutations.

### Forms

All forms use Server Actions + `useActionState`:

```typescript
// actions/createTeamAction.ts
"use server";
export async function createTeamAction(prevState: unknown, formData: FormData) {
  const parsed = createTeamSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten().fieldErrors };
  await db.insert(teams).values(parsed.data);
  revalidatePath("/dashboard");
  return { success: true };
}

// Component
"use client";
import { useActionState } from "react";
export function CreateTeamForm() {
  const [state, action] = useActionState(createTeamAction, null);
  // ...
}
```

## What We Don't Do (and Why)

| Anti-pattern | Why not |
|-------------|---------|
| `useEffect` for data fetching | Causes waterfall requests, breaks SSR, doubles network calls |
| API routes for internal mutations | Server Actions are simpler, typesafe, no fetch boilerplate |
| `any` type | Defeats TypeScript — if you must, use `unknown` + type guard |
| Raw SQL outside migrations | Loses type safety, harder to refactor |
| `/* @ts-expect-error */` | Papering over problems — fix the types or use a type assertion with comment |
| Barrel exports (`index.ts` re-exporting everything) | Kills tree-shaking, slows dev server, circular dependency risk |
| `console.log` in production code | Use a logger (pino) or remove — never ship debug logs |
| Inline styles / CSS-in-JS | Tailwind is the standard — one-off styles go in `@apply` or global CSS |
| Direct `fetch()` to external APIs in components | Creates slow renders — move to Server Components or background jobs |
| `.env` committed to git | Use `.env.example` with dummy values — real secrets in Vercel dashboard |

## Dev Commands

```bash
npm run dev           # Next.js dev server (localhost:3000)
npm run build         # Production build
npm run lint          # ESLint + Prettier check
npm run format        # Prettier write
npm run db:generate   # Generate migration from schema changes
npm run db:migrate    # Apply pending migrations
npm run db:studio     # Open Drizzle Studio (localhost:4983)
npm run test          # vitest (unit + integration)
npm run test:e2e      # Playwright (E2E)
```

## Environment Variables

```bash
# .env.example — copy to .env.local for development
DATABASE_URL="data.db"            # SQLite file path
STRIPE_SECRET_KEY="sk_test_..."   # Stripe test mode
STRIPE_WEBHOOK_SECRET="whsec_..." # Stripe webhook signing secret
AUTH_SECRET="openssl rand -hex 32"
AUTH_GOOGLE_ID=""                 # Google OAuth (optional)
AUTH_GOOGLE_SECRET=""
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```
