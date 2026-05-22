# CLAUDE.md — Next.js 15 + SQLite project

Drop this at the repo root. Claude Code reads it on every session. Sections below are calibrated for a greenfield SaaS using **Next.js 15 App Router** + **better-sqlite3** (sync, embedded) + **drizzle-orm**. Substitute Turso libsql client if you need remote DB; everything else stays.

---

## Stack & versions

| Layer | Choice | Version | Why this and not the alternative |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | App Router only — `pages/` is legacy. RSC + Server Actions remove >80% of API boilerplate. |
| Language | TypeScript | 5.6+ strict | `strict: true`, `noUncheckedIndexedAccess: true`. No `any`. |
| Runtime | Node | 22 LTS | Native fetch, perf parity with edge, no polyfills. |
| DB | better-sqlite3 | 11.x | Synchronous — fits the Server Component model. ~zero latency vs Postgres locally. |
| ORM | drizzle-orm + drizzle-kit | latest | Type-safe SQL, no codegen at runtime, plays well with SQLite. **No Prisma** (heavy generated client, painful migrations). |
| Styling | Tailwind CSS | 4.x | No CSS-in-JS — RSC-incompatible. |
| Auth | `next-auth` v5 (Auth.js) | beta is fine | Cookie sessions in SQLite. No third-party auth provider lock-in. |
| Tests | Vitest + Playwright | latest | Vitest for units (fast, ESM-native). Playwright for e2e. **No Jest.** |
| Lint | ESLint + `eslint-plugin-drizzle` | latest | Drizzle plugin catches `delete()` / `update()` without `where()`. |
| Format | Prettier (no opinions) | latest | Default config. Stop bikeshedding. |
| Pkg mgr | pnpm | 9.x | Faster, content-addressable, monorepo-safe. |

Bring this exact list to project init. Don't substitute without leaving a note in this file explaining why.

---

## Folder structure

```
.
├── app/                          # Next.js App Router root
│   ├── (marketing)/              # Public, statically-rendered pages — landing, pricing, blog
│   │   └── page.tsx
│   ├── (app)/                    # Authenticated dashboard (uses middleware)
│   │   ├── layout.tsx            # Server-side session check + nav shell
│   │   └── dashboard/
│   ├── api/                      # Route handlers — used ONLY for webhooks / external POST endpoints
│   │   └── stripe/route.ts
│   ├── actions/                  # Server Actions (mutations). Default mutation path.
│   │   └── *.ts
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                       # Headless / primitive — Button, Input, Dialog. Pure RSC where possible.
│   └── feature/                  # Feature-scoped — DashboardSidebar, UserAvatar
├── lib/
│   ├── db/
│   │   ├── index.ts              # Drizzle client singleton
│   │   ├── schema.ts             # All table definitions
│   │   └── migrate.ts            # Script: applies pending migrations to ./data/app.db
│   ├── auth.ts                   # next-auth config
│   ├── env.ts                    # Zod-validated env. Throws at boot if missing.
│   └── utils.ts                  # `cn()` + tiny shared helpers
├── drizzle/
│   ├── 0001_initial.sql          # Hand-edited after `drizzle-kit generate` — see migration rules below
│   ├── 0002_add_billing.sql
│   └── meta/                     # Drizzle bookkeeping — commit this, don't gitignore
├── data/
│   └── app.db                    # SQLite file. Gitignored. Production uses persistent volume mount.
├── tests/
│   ├── unit/                     # Vitest — colocated allowed too via *.test.ts beside source
│   └── e2e/                      # Playwright
├── public/
├── drizzle.config.ts
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── CLAUDE.md                     # ← this file
```

**Rules:**

- Routes live in `app/`. Anything you'd reach via URL.
- Reusable React in `components/`. Never put a route there.
- Anything imported by both routes and Server Actions goes in `lib/`.
- `actions/` holds Server Actions. **Use these instead of `/api` handlers for in-app mutations** — type-safe, no fetch needed, smaller bundle.
- `/api` is for *external* POST destinations (Stripe webhooks, OAuth callbacks). Not for the frontend to call.

---

## Dev commands

```bash
pnpm install
pnpm dev                          # Next.js dev on http://localhost:3000

# Database
pnpm db:generate                  # drizzle-kit generate (creates new drizzle/NNNN_*.sql)
pnpm db:migrate                   # apply pending migrations to data/app.db
pnpm db:studio                    # drizzle-kit studio — visual DB browser

# Quality
pnpm lint                         # eslint --fix
pnpm typecheck                    # tsc --noEmit
pnpm test                         # vitest run
pnpm test:e2e                     # playwright test

# Production
pnpm build && pnpm start          # build + start; do NOT use turbo for prod
```

The `package.json` should have every script above. If it doesn't, add it.

---

## SQL / migration conventions

1. **Migrations are append-only.** Once `0001_initial.sql` is committed to `main`, **never edit it**. Add a new migration file (`0002_*.sql`) for any change.
2. **Generate, then hand-tune.** `pnpm db:generate` produces a draft. Open it, rename ambiguous defaults, add explicit `ON DELETE` clauses, write a one-line comment at the top describing the migration in plain English.
3. **Every migration must be reversible** — include a `-- DOWN` section at the bottom with the inverse statements, even if drizzle-kit doesn't enforce it. Future-you will need it.
4. **Foreign keys are explicit.** SQLite foreign keys are off by default. We turn them on in `lib/db/index.ts` via `db.pragma('foreign_keys = ON')`. Every FK definition uses `references(() => parentTable.id, { onDelete: 'cascade' | 'set null' | 'restrict' })` — pick one consciously.
5. **Use `text` for IDs.** `id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID())`. Avoid integer `autoincrement` — leaks row counts in URLs.
6. **Timestamps are `integer` (Unix epoch).** `createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date())`. Drizzle converts to Date for you. SQLite has no native datetime.
7. **No raw SQL in routes / components.** All DB access goes through drizzle queries in a `lib/db/queries/*.ts` file. Easier to mock, lint, and refactor.
8. **Indexes are intentional.** Don't blanket-index everything. Add an index only after a slow query exists. Comment WHY in the migration.

Example skeleton (`drizzle/0002_add_posts.sql`):

```sql
-- Adds posts table. Posts belong to users; cascade-delete on user removal.
CREATE TABLE `posts` (
    `id` TEXT PRIMARY KEY NOT NULL,
    `user_id` TEXT NOT NULL REFERENCES `users`(`id`) ON DELETE CASCADE,
    `title` TEXT NOT NULL,
    `body` TEXT NOT NULL,
    `created_at` INTEGER NOT NULL
);

CREATE INDEX `posts_user_id_idx` ON `posts`(`user_id`);
-- ↑ supports the "list this user's posts" query in lib/db/queries/posts.ts

-- DOWN
DROP TABLE `posts`;
```

---

## Component patterns

**Default to Server Components.** Add `'use client'` only when you genuinely need:

- Interactive state (`useState`, `useReducer`)
- Browser APIs (`window`, `localStorage`, `IntersectionObserver`)
- Event handlers on user elements
- Third-party libs that touch the DOM

If those aren't needed → don't make it a Client Component. Pushing data fetching to Server Components removes round trips and eliminates loading spinners for above-the-fold content.

### Data fetching

- Server Component: `await db.select(...).from(table)` directly. No `useEffect`, no API call.
- Client Component needing data: pass it from a parent Server Component as a prop, **not** by fetching from inside the client.
- Mutations: Server Actions. Forms use `action={mySAction}`. No `fetch('/api/...')` from the frontend.

### Component file shape

```tsx
// components/feature/UserProfile.tsx — Server Component (no 'use client')
import { db } from '@/lib/db'
import { users } from '@/lib/db/schema'
import { eq } from 'drizzle-orm'
import { AvatarMenu } from './AvatarMenu' // Client Component sibling

export async function UserProfile({ userId }: { userId: string }) {
    const user = await db.select().from(users).where(eq(users.id, userId)).get()
    if (!user) return null
    return (
        <div className="flex items-center gap-3">
            <AvatarMenu user={user} />          {/* interactivity isolated */}
            <span>{user.name}</span>
        </div>
    )
}
```

### Forms

```tsx
// app/actions/posts.ts — Server Action
'use server'
import { db } from '@/lib/db'
import { posts } from '@/lib/db/schema'
import { revalidatePath } from 'next/cache'
import { z } from 'zod'

const schema = z.object({ title: z.string().min(1), body: z.string().min(1) })

export async function createPost(formData: FormData) {
    const parsed = schema.safeParse(Object.fromEntries(formData))
    if (!parsed.success) return { error: parsed.error.flatten() }
    const session = await auth()             // next-auth
    if (!session?.user) return { error: 'unauth' }
    await db.insert(posts).values({
        id: crypto.randomUUID(),
        userId: session.user.id,
        title: parsed.data.title,
        body: parsed.data.body,
    })
    revalidatePath('/dashboard/posts')
}
```

```tsx
// app/(app)/dashboard/posts/new/page.tsx
import { createPost } from '@/app/actions/posts'
export default function NewPostPage() {
    return (
        <form action={createPost} className="space-y-3">
            <input name="title" required />
            <textarea name="body" required />
            <button type="submit">Create</button>
        </form>
    )
}
```

No client-side state needed for this form. No `useState`. No fetch. The whole thing renders on the server, submits via Server Action, revalidates the parent path.

---

## What we don't do (and why)

| ❌ Don't | ✅ Instead | Reason |
|---|---|---|
| `fetch('/api/...')` from a client component to query our own backend | Server Action (mutation) OR Server Component data fetch (read) | Round trips, no type-safety, bundle bloat, manual error handling. Server Actions are typed end-to-end. |
| Prisma | drizzle-orm | Prisma generates a runtime client (slow cold start, heavy node_modules), proprietary schema lang, painful SQLite migrations. Drizzle is plain TypeScript + plain SQL. |
| Mongoose / Mongo | SQLite (or Postgres later) | Document DBs sound flexible until you need relational queries, which is always. SQLite + Drizzle covers >95% of SaaS data shapes. |
| Edit committed migration files | Add a new migration | Editing breaks every collaborator's local DB. Always append. |
| Auto-increment integer IDs in URLs | `crypto.randomUUID()` text IDs | Sequential IDs leak business metrics (user count, growth rate). |
| `any` types | Define the actual type, or `unknown` + narrow | `any` is the silent-bug supplier. `strict: true` exists for a reason. |
| `useEffect` for data fetching | Server Component / Server Action / SWR (only when neither fits) | useEffect data fetch is the worst tradeoff possible — loading flicker, no SSR, manual deps array. |
| CSS-in-JS (styled-components, emotion) | Tailwind | RSC-incompatible. CSS Modules also OK but more boilerplate. |
| Global state libraries (Redux, Zustand) for server state | URL params, RSC props, Server Actions, `revalidatePath` | The DB is the source of truth — don't mirror it client-side. Client state only for genuinely-client things (modal open/closed, draft form text). |
| `app/api/*` route handlers for our own frontend's mutations | Server Actions | Route handlers add a network hop + serialization for no benefit. |
| Anonymous default exports | Named exports | Refactor-safe, IDE rename works, no `export default function () {}` mystery. |
| `console.log` in committed code | Structured logger (pino) or remove | Console.log in prod is noise + leaks data. Strip before commit. |
| Mixing `pages/` and `app/` | App Router only | Two routing systems = double the bugs. |
| Auto-format on save changing line endings | Configure `.gitattributes` (`* text=auto eol=lf`) | Cross-OS LF/CRLF flips clog every diff. |
| Skipping Zod on form input / external JSON | Zod on every boundary | Server Actions trust the FormData blindly otherwise. One bad client = corrupt DB. |
| `try { ... } catch (e) { console.error(e) }` swallowing | Either rethrow or log + return typed error from a Server Action | Silent catches are how production bugs survive. |

---

## Quick reference for Claude

When you write or edit code in this project:

- Reach for a **Server Component** first; only escalate to `'use client'` when something on the list above forces it.
- Mutations → **Server Action**, not a route handler.
- Validate input with **Zod** before touching the DB.
- Every DB query goes through `lib/db/queries/*.ts`. No raw `db.select` in route files.
- For new tables, write the migration in `drizzle/NNNN_*.sql` and add a one-line top comment explaining why.
- After a migration, run `pnpm db:migrate` then update any affected query files.
- For new routes, prefer route groups `(marketing)` / `(app)` over deep folder nesting.
- If you add a new dependency, also update the "Stack & versions" table above with the *why*.

If something here gets in the way of a feature, **document the exception in the PR description** — don't silently break the pattern.
