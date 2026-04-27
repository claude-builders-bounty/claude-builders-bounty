# 🏗️ CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Opinionated conventions for a production SaaS. Every rule has a reason.

## 📁 Project Structure

```
src/
├── app/                    # App Router pages
│   ├── (auth)/             # Auth layout (sign-in, sign-up)
│   ├── (dashboard)/        # Dashboard layout (requires auth)
│   ├── api/                # Route handlers
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # Atomic UI (shadcn-style)
│   ├── forms/              # React Hook Form wrappers
│   └── layout/             # Sidebar, navbar, etc.
├── db/
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # Auto-generated
│   └── index.ts            # DB connection (singleton)
├── lib/
│   ├── auth.ts             # Lucia/Auth.js config
│   ├── stripe.ts           # Stripe client
│   └── email.ts            # Resend/SendGrid
├── actions/                # Server Actions (one file per domain)
│   ├── user.actions.ts
│   └── billing.actions.ts
└── types/
    └── index.ts            # Shared TypeScript types
```

**Why flat actions folder?** Server Actions are the primary data layer. Co-locating with "services" or "api" creates confusion. File-per-domain keeps imports predictable.

## 🗄️ DB Migrations (Drizzle + SQLite)

```bash
pnpm db:generate   # Generate migration from schema changes
pnpm db:migrate    # Apply pending migrations
pnpm db:seed       # Seed development data
```

**Rules:**
- **NEVER delete a migration file** after it's been applied in any environment. Write a new migration instead.
- **ALWAYS run `db:generate` before `db:migrate`** — they are not the same command.
- **Seed data goes in `db/seed.ts`**, not embedded in migrations.
- **Use `integer` for timestamps** (`unixepoch() * 1000`), not SQLite's native datetime text.
- **Use `text` for IDs** (CUID2), not auto-increment integers — they leak entity count.

## 🔐 Auth Conventions

- **Session-based auth** (Lucia v3 or Auth.js v5), never JWT-only for SaaS
- **Middleware in `src/middleware.ts`** — protect dashboard routes, redirect to login
- **Auth helper in `src/lib/auth.ts`** — expose `getSession()` and `requireAuth()`
- **`requireAuth()` throws redirect** — do NOT return null, let the middleware/error boundary handle it

**Anti-pattern:** Checking auth inside every page component. Use layout-level auth.

## 🧱 Component Rules

| Pattern | Do ✅ | Don't ❌ |
|---------|-------|---------|
| State | Server Components by default | `"use client"` on every page |
| Forms | React Hook Form + Zod | Raw `useState` for form data |
| Data fetching | Server Component `async` | `useEffect` + fetch |
| Mutations | Server Actions | API routes (use for webhooks only) |
| Styling | Tailwind CSS classes | CSS modules |
| UI lib | shadcn/ui (copy-paste) | Full component library import |

**Server Action Pattern:**
```ts
// actions/user.actions.ts
"use server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/db";
import { users } from "@/db/schema";
import { z } from "zod";

const updateProfileSchema = z.object({
  name: z.string().min(1).max(50),
});

export async function updateProfile(formData: FormData) {
  const user = await requireAuth();
  const parsed = updateProfileSchema.parse(Object.fromEntries(formData));
  await db.update(users).set(parsed).where(eq(users.id, user.id));
  revalidatePath("/dashboard/settings");
}
```

## 📊 Database Access Patterns

**Who writes SQL:** You (Drizzle ORM), not raw SQLite CLI
**Why:** Migrations allow rollback, schema tracking, and type safety

```ts
// ✅ Good: typed query with Drizzle
const projects = await db.select().from(projects).where(eq(projects.userId, user.id));

// ❌ Bad: raw SQL in app code (no type safety, no migration tracking)
const projects = db.run("SELECT * FROM projects WHERE user_id = ?", [user.id]);
```

**Transaction pattern for multi-table writes:**
```ts
await db.transaction(async (tx) => {
  await tx.insert(orders).values(orderData);
  await tx.update(inventory).set({ stock: sql`stock - 1` });
});
```

## 🚀 Dev Commands

```bash
pnpm dev         # Next.js dev server
pnpm build       # Production build (run before pushing)
pnpm lint        # ESLint + Prettier check
pnpm typecheck   # tsc --noEmit (separate from build)
pnpm test        # Vitest
pnpm test:e2e    # Playwright
```

**Pre-push checklist:**
1. `pnpm typecheck` — no TS errors
2. `pnpm build` — no build errors (SQLite WASM requires Node build)
3. `pnpm lint` — no lint warnings
4. `git diff --stat` — review what changed

## 🏷️ Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | kebab-case | `user-settings.tsx` |
| Components | PascalCase | `UserSettings.tsx` |
| Functions (non-react) | camelCase | `formatCurrency()` |
| Server Actions | verbNoun | `updateProfile()` |
| DB tables | plural snake_case | `user_sessions` |
| DB columns | snake_case | `created_at` |
| Env vars | UPPER_SNAKE | `DATABASE_URL` |

## ⚠️ Common Gotchas

- **SQLite does NOT have enums** — use `text` with Zod validation at the app layer
- **SQLite does NOT support `ALTER COLUMN`** — create new column, migrate data, drop old
- **Next.js `redirect()` throws** — it's a Next.js navigation, not HTTP redirect. Wrap in try/catch if needed
- **Server Actions are POST** — you cannot call them from `Link` or `a` tags
- **Revalidation is explicit** — calling `revalidatePath()` is not optional after mutations
- **`cookies()` is dynamic** — marking a page `export const dynamic = "force-static"` will break cookie-based auth

## 🧪 Testing Strategy

1. **Unit**: Test pure functions (utilities, formatters, validation schemas)
2. **Integration**: Test Server Actions (call them directly with `msw` for DB)
3. **E2E**: Test critical flows (auth, billing, CRUD)

```ts
// actions/__tests__/user.actions.test.ts
import { describe, it, expect } from "vitest";

describe("updateProfile", () => {
  it("rejects empty name", async () => {
    await expect(updateProfile(new FormData())).rejects.toThrow();
  });
});
```

---

> **Why this opinionated?** Next.js 15 + SQLite is powerful but has sharp edges: SQLite's lack of enum/alter support, App Router's auth patterns, and Server Action's POST-only nature. These conventions exist because we've hit every one of these footguns.
