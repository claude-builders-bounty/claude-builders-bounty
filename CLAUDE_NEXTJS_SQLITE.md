# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Copy this file to the root of your project as `CLAUDE.md`.
Every rule here has a reason. Nothing is generic filler.

---

## Stack

- **Framework:** Next.js 15 (App Router, React 19)
- **Database:** SQLite via `better-sqlite3` (local) or `@libsql/client` (Turso in prod)
- **ORM:** Drizzle ORM — schema-first, type-safe, no magic
- **Auth:** next-auth v5 (Auth.js) with database sessions
- **Styling:** Tailwind CSS v4
- **Runtime:** Node.js — no edge runtime

---

## Project Structure

```
/app                   Next.js App Router pages and layouts
  /api                 Route handlers (API endpoints)
  /(auth)              Auth pages (login, signup) — in a route group
  /(dashboard)         Authenticated app pages — in a route group
  /layout.tsx          Root layout (fonts, providers, metadata)
/components            Shared UI components — dumb, presentational only
/lib
  /db                  Database layer — ALL db access lives here
    schema.ts          Drizzle table definitions
    index.ts           DB client singleton
    /queries           One file per entity (users.ts, posts.ts, etc.)
  /auth                next-auth config and session utilities
  /utils               Pure helper functions (no side effects, no I/O)
/hooks                 Client-side React hooks
/types                 Shared TypeScript types (not Drizzle schemas)
drizzle.config.ts      Drizzle Kit config — points at schema.ts
```

**Rule:** No database queries outside `/lib/db/`. Server actions, route handlers, and
page components call `/lib/db/queries/` functions — never raw SQL inline.

---

## Dev Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run db:push      # Push schema changes to dev SQLite (no migration file)
npm run db:migrate   # Generate + apply migration (use for prod)
npm run db:studio    # Open Drizzle Studio at localhost:4983
npm run lint         # ESLint
npm run type-check   # tsc --noEmit
npm run build        # Production build
```

---

## Database Rules

### Schema (drizzle/schema.ts)

```typescript
import { sql } from "drizzle-orm";
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});
```

**Rules:**
- All IDs are `text` UUIDs generated with `crypto.randomUUID()` — never auto-increment integers
- Timestamps are `integer` with `mode: "timestamp"` — stored as Unix seconds, not ISO strings
- Column names are `snake_case` in the DB; Drizzle maps to `camelCase` in TS automatically
- Every table has `createdAt`; mutable rows also get `updatedAt`
- Add `updatedAt` with a Drizzle `$onUpdate()` hook, not a DB trigger

### Migrations

- **Development:** use `npm run db:push` — fast, no migration files, safe to use
- **Production / staging:** use `npm run db:migrate` — generates a versioned SQL file in `drizzle/`
- **Never edit migration files by hand** — regenerate if the schema is wrong
- **Never delete migration files** — they form the history

### Query Files

```typescript
// lib/db/queries/users.ts
import { eq } from "drizzle-orm";
import { db } from "../index";
import { users } from "../schema";

export async function getUserByEmail(email: string) {
  return db.query.users.findFirst({ where: eq(users.email, email) });
}

export async function createUser(email: string) {
  const [user] = await db.insert(users).values({ email }).returning();
  return user;
}
```

**Rule:** One function per operation. No generic "repository" classes. Functions are
imported directly by server actions and route handlers.

---

## Server Actions vs Route Handlers

| Use case | Use |
|----------|-----|
| Form submissions, mutations from client components | Server Action (`"use server"`) |
| Webhooks, external API calls, file downloads | Route Handler (`/app/api/`) |
| Data loading in page/layout | `async` Server Component, no fetch needed |

**Server Actions:**
```typescript
// app/(dashboard)/actions.ts
"use server";
import { auth } from "@/lib/auth";
import { createPost } from "@/lib/db/queries/posts";

export async function createPostAction(formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");
  const title = formData.get("title") as string;
  return createPost(session.user.id, title);
}
```

**Rule:** Always check session in server actions before any DB write. Never trust
client-supplied user IDs — always read from the server session.

---

## Auth

- Sessions are stored in the SQLite DB (not JWT) — this gives you instant revocation
- `auth()` from next-auth is the only way to get the current user in server code
- `useSession()` is the only way to get it in client components
- Never expose raw user IDs in URLs — use opaque slugs or verify ownership server-side

```typescript
// lib/auth/index.ts
export { auth, handlers, signIn, signOut } from "./config";

// To protect a page:
// app/(dashboard)/layout.tsx
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardLayout({ children }) {
  const session = await auth();
  if (!session) redirect("/login");
  return <>{children}</>;
}
```

---

## Component Patterns

**Server Components** (default — no `"use client"`):
- Fetch data directly from `/lib/db/queries/` — no `fetch()` needed
- Render HTML; pass serializable props to client children
- No hooks, no event handlers

**Client Components** (`"use client"` at top):
- Only for interactivity (forms, modals, state, effects)
- Receive data as props; fetch via server actions or route handlers
- Keep them small — push logic up to server components

**Rule:** If a component doesn't need `useState`, `useEffect`, or event handlers,
it's a server component. Don't add `"use client"` by default.

---

## Anti-Patterns to Avoid

| Don't | Do instead |
|-------|-----------|
| `fetch("/api/users")` inside a server component | Call `getUsers()` from `/lib/db/queries/users.ts` directly |
| Database queries in components | Put all DB access in `/lib/db/queries/` |
| `useEffect` to load data on mount | Load in a server component and pass as prop |
| `any` types | Write the type; use `unknown` if truly unknown |
| Raw `sql` strings | Use Drizzle's query builder; `sql` only for complex aggregates |
| Storing sensitive data in localStorage | Use HTTP-only cookies (next-auth handles this) |
| Auto-increment integer IDs | UUID text IDs |
| `db:push` in production | `db:migrate` for production |

---

## Naming Conventions

- **Files:** `kebab-case.ts` for everything except components
- **Components:** `PascalCase.tsx`
- **Functions:** `camelCase` — verb-first for actions (`createUser`, `getUserByEmail`)
- **Types/Interfaces:** `PascalCase`, no `I` prefix
- **DB columns:** `snake_case` (Drizzle maps them automatically)
- **Environment variables:** `SCREAMING_SNAKE_CASE`; all secrets in `.env.local`, never `.env`

---

## Environment Variables

```bash
# .env.local (never commit this)
DATABASE_URL="file:./local.db"           # local SQLite file
TURSO_DATABASE_URL="libsql://..."        # Turso prod URL
TURSO_AUTH_TOKEN="..."                   # Turso auth token
AUTH_SECRET="..."                        # next-auth secret (generate with: openssl rand -base64 32)
AUTH_GITHUB_ID="..."                     # OAuth app credentials
AUTH_GITHUB_SECRET="..."
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

**Rule:** `NEXT_PUBLIC_` prefix only for values the browser must see. Everything
else is server-only. Never log environment variables.

---

## Testing Approach

- **Unit tests:** Vitest for pure utility functions in `/lib/utils/`
- **Integration tests:** Test server actions by calling them directly with a real SQLite DB
  (use an in-memory `:memory:` DB in tests, migrate schema in `beforeAll`)
- **E2E:** Playwright for critical auth flows and payment flows only
- **No mocking the database** — use a real in-memory SQLite instance in tests

---

## Key Files to Check First

When debugging or adding features, check in this order:

1. `drizzle/schema.ts` — what tables exist and their types
2. `lib/db/queries/` — what DB operations are already written
3. `lib/auth/config.ts` — auth providers and session shape
4. `app/(dashboard)/` — where the authenticated pages live
5. `app/api/` — existing route handlers

---

*This CLAUDE.md is opinionated for a reason: consistency beats flexibility for solo
and small-team SaaS. Follow these rules and Claude Code will navigate the codebase
without asking clarifying questions.*
