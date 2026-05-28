# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **Purpose**: This file gives Claude Code full project context so it can work autonomously without asking clarifying questions. Paste this into the root of any greenfield Next.js 15 App Router + SQLite project.

---

## Stack & Versions

| Layer       | Choice                     | Version  | Why                                   |
|-------------|----------------------------|----------|---------------------------------------|
| Framework   | Next.js (App Router)       | 15.x     | RSC, streaming, server actions       |
| Runtime     | Node.js                    | >=20 LTS | ESM support, stable fetch API        |
| Database    | better-sqlite3             | 11.x     | Synchronous, zero-config, fast       |
| ORM         | Drizzle ORM                | 0.x      | Type-safe SQL, SQLite-native         |
| Auth        | next-auth v5               | 5.x      | App Router native, session cookies   |
| Styling     | Tailwind CSS               | 4.x      | Utility-first, no runtime cost       |
| Validation  | Zod                        | 3.x      | Runtime schema validation            |
| Testing     | Vitest + Testing Library   | latest   | Fast, ESM-native                     |
| Linting     | Biome                      | latest   | Fast formatter + linter in one tool  |

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Protected route group
│   │   ├── layout.tsx      # Auth guard + sidebar
│   │   ├── page.tsx        # Dashboard home
│   │   ├── settings/
│   │   └── billing/
│   ├── api/                # Route handlers (REST)
│   │   ├── webhook/route.ts
│   │   └── stripe/route.ts
│   ├── layout.tsx          # Root layout (html, body, fonts)
│   ├── page.tsx            # Landing / marketing page
│   └── globals.css
├── components/
│   ├── ui/                 # Shadcn-style primitives (Button, Dialog, etc.)
│   └── features/           # Domain-specific components
├── lib/
│   ├── db/
│   │   ├── index.ts        # Drizzle client singleton
│   │   ├── schema.ts       # All table definitions
│   │   └── migrations/     # SQL migration files
│   ├── auth.ts             # next-auth config
│   ├── stripe.ts           # Stripe client helper
│   └── utils.ts            # cn(), formatDate(), etc.
├── server/
│   ├── queries/            # Typed DB query functions
│   └── actions/            # Server actions (use server)
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types
└── test/
    ├── setup.ts            # Vitest setup (in-memory SQLite)
    └── *.test.ts
```

**Rules**:
- Every file exports exactly one main thing (component, function, type).
- Colocate tests next to source: `utils.test.ts` next to `utils.ts`.
- Route groups `(auth)`, `(dashboard)` control layout — never nest deeper than 2 levels.

---

## Dev Commands

```bash
npm run dev          # Start dev server (turbo, port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run test         # Run all tests (Vitest)
npm run test:watch   # Run tests in watch mode
npm run db:generate  # Generate Drizzle migration SQL
npm run db:migrate   # Apply migrations to local DB
npm run db:studio    # Open Drizzle Studio (DB browser)
npm run lint         # Biome check + fix
npm run typecheck    # tsc --noEmit
```

---

## SQL / Migration Conventions

1. **One migration per logical change** — never bundle unrelated schema changes.
2. **Migration file names**: `0001_create_users_table.sql` (zero-padded, descriptive).
3. **All columns have NOT NULL + DEFAULT** where possible. No nullable columns without explicit reason.
4. **Timestamps**: `created_at TEXT DEFAULT (datetime('now'))` — always TEXT in ISO 8601.
5. **Foreign keys**: Always `REFERENCES … ON DELETE CASCADE` unless data must be preserved.
6. **No raw SQL in route handlers** — all DB access goes through `server/queries/` or `server/actions/`.
7. **Schema lives in one file** (`lib/db/schema.ts`). Split only when >300 lines.
8. **Drizzle `sqliteTable`** is the source of truth. Generate migrations from it, never hand-edit SQL.

### Example schema definition

```typescript
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),           // nanoid, never auto-increment
  email: text("email").notNull().unique(),
  name: text("name").notNull().default(""),
  plan: text("plan", { enum: ["free", "pro", "enterprise"] }).notNull().default("free"),
  createdAt: text("created_at").notNull().default(sql`(datetime('now'))`),
});
```

---

## Component Patterns

1. **Server Components by default** — only add `"use client"` when you need interactivity (useState, useEffect, event handlers).
2. **Server Actions for mutations** — never write API routes for form submissions. Use `use server` functions in `server/actions/`.
3. **Props: plain objects, no callbacks** — Server Components receive serializable data only.
4. **UI components in `components/ui/`** — stateless, composable, accept `className` via `cn()`.
5. **Feature components in `components/features/`** — may hold state, compose UI primitives.
6. **Loading states**: Use `loading.tsx` (Suspense boundary) — never add client-side loading spinners manually.
7. **Error states**: Use `error.tsx` boundary at route group level.

### Example server action

```typescript
"use server";

import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";

const updateNameSchema = z.object({
  userId: z.string(),
  name: z.string().min(1).max(100),
});

export async function updateName(formData: FormData) {
  const { userId, name } = updateNameSchema.parse({
    userId: formData.get("userId"),
    name: formData.get("name"),
  });

  await db.update(users).set({ name }).where(eq(users.id, userId));
  revalidatePath("/settings");
}
```

---

## What We Don't Do (and Why)

| We don't                         | Because                                    | Instead                              |
|----------------------------------|--------------------------------------------|--------------------------------------|
| Use Prisma                       | Drizzle is lighter, generates better SQL   | Drizzle ORM                          |
| Use `getServerSideProps`         | Deprecated in App Router                   | Server Components + `fetch()`        |
| Store files in the repo          | SQLite DB should be `.gitignore`d          | Use `DATABASE_URL` env var           |
| Use `any` type                   | Defeats TypeScript's purpose               | Proper types or `unknown` + narrow   |
| Use CSS modules or styled-jsx    | Tailwind handles all styling               | Tailwind utility classes             |
| Use `pages/` directory           | App Router is the standard                 | `app/` directory only                |
| Create REST API routes for CRUD  | Server Actions are simpler, type-safe      | `"use server"` functions             |
| Use `eslint` + `prettier`        | Biome replaces both, runs 10× faster       | Biome (`npm run lint`)               |
| Use `uuid` for IDs               | Extra dependency for something simple      | `nanoid` (7 chars, URL-safe)         |

---

## Anti-Patterns to Avoid

1. **Don't import server code in client code** — `lib/db/*`, `server/*` must never appear in `"use client"` files. Use server actions as the bridge.
2. **Don't use `useEffect` for data fetching** — use Server Components to fetch data at render time.
3. **Don't create "god" components** — if a component >150 lines, split it.
4. **Don't use inline SQL strings** — always use Drizzle query builder.
5. **Don't skip input validation** — every server action and API route must validate with Zod before processing.
6. **Don't hardcode secrets** — all config via `process.env` + a single `lib/env.ts` validated schema.
7. **Don't use `console.log` in production** — use a structured logger or remove before merge.

---

## Environment Variables

Create a `.env.local` file (never committed):

```env
DATABASE_URL=./data/app.db
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<openssl rand -base64 32>
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Validate at startup via `lib/env.ts`:

```typescript
import { z } from "zod";

export const env = z.object({
  DATABASE_URL: z.string().min(1),
  NEXTAUTH_URL: z.string().url(),
  NEXTAUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
}).parse(process.env);
```

---

## Testing Conventions

1. **In-memory SQLite for tests** — `:memory:` DB, schema applied per test suite.
2. **One test file per module** — `utils.test.ts` tests `utils.ts`.
3. **Test structure**: Arrange → Act → Assert. No nested describes >2 levels deep.
4. **Mock external services** (Stripe, email) — never hit real APIs in tests.
5. **Server action tests** use the actual DB (in-memory), not mocks.

```typescript
// Example test
import { describe, it, expect, beforeEach } from "vitest";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { getUserById } from "@/server/queries/users";

beforeEach(() => {
  db.delete(users).run(); // Clean slate
});

describe("getUserById", () => {
  it("returns the user when found", async () => {
    db.insert(users).values({ id: "abc", email: "test@example.com" }).run();
    const user = getUserById("abc");
    expect(user?.email).toBe("test@example.com");
  });
});
```

---

## Git & PR Conventions

- **Branch names**: `feat/short-description`, `fix/short-description`
- **Commit messages**: Conventional Commits (`feat: add billing page`, `fix: null check on user query`)
- **PR size**: ≤400 lines changed. If bigger, split into stacked PRs.
- **Every PR includes a test** for the new or fixed behavior.

---

*This CLAUDE.md is opinionated by design. If something doesn't fit your project, change the rule and document why.*
