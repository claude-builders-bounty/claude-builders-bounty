# CLAUDE.md — Next.js 15 + SQLite SaaS

> Production-ready conventions for a SaaS built with Next.js 15 App Router and SQLite.
> This file tells Claude Code everything it needs to work in this repo without guessing.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | Server Components by default; RSC for data fetching |
| Runtime | Node.js | 20 LTS | Stable, ESM-native |
| Language | TypeScript | 5.x | `strict: true`, no `any` escapes |
| Database | better-sqlite3 | 11.x | Embedded, zero-config, synchronous (perfect for edge-free SaaS) |
| Migrations | custom `scripts/migrate.ts` | — | SQL files in `db/migrations/`, run in sorted order |
| ORM | None | — | Raw SQL via better-sqlite3. ORMs hide SQLite's strengths. |
| Auth | NextAuth v5 (Auth.js) | 5.x | Session-based, works with App Router middleware |
| Styling | Tailwind CSS | 4.x | Utility-first, co-located with components |
| Validation | Zod | 3.x | Runtime + compile-time types from one schema |
| Testing | Vitest | 2.x | Fast, native ESM, good Next.js support |
| Package Manager | pnpm | 9.x | Strict, fast, disk-efficient |

### What we don't use (and why)

- **Prisma / Drizzle** — adds abstraction over SQLite that hides control. We write SQL directly because SQLite rewards it: `RETURNING`, CTEs, `json_each()`, `json_group_array()` are too useful to abstract away.
- **Redux / Zustand** — Server Components fetch data. Client state is minimal. Use `useState` + URL params.
- **CSS-in-JS** — runtime cost for zero benefit. Tailwind is compile-time.
- **Pages Router** — App Router is the present. No hybrid.
- **ORM-generated types** — we define Zod schemas first, derive types from those. Single source of truth.

---

## Project Structure

```
.
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Route group: login, register, forgot-password
│   │   ├── login/page.tsx
│   │   └── layout.tsx           # Auth layout (centered card, no nav)
│   ├── (dashboard)/             # Route group: main app (behind auth)
│   │   ├── layout.tsx           # Dashboard layout (sidebar + topbar)
│   │   ├── page.tsx             # Dashboard home / overview
│   │   └── settings/page.tsx
│   ├── api/                     # API routes (only when RSC can't do it)
│   │   └── webhooks/            # External webhook handlers
│   ├── layout.tsx               # Root layout (html, body, fonts, providers)
│   └── page.tsx                 # Landing / marketing page
├── components/
│   ├── ui/                      # Generic, reusable, no business logic
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── dialog.tsx
│   └── features/                # Business-specific components
│       ├── auth/login-form.tsx
│       └── dashboard/stats-card.tsx
├── db/
│   ├── migrations/              # 001_create_users.sql, 002_add_tasks.sql
│   ├── schema.sql               # Current schema (auto-generated from migrations)
│   ├── seed.ts                  # Dev seed data
│   └── index.ts                 # Database connection singleton
├── lib/
│   ├── auth.ts                  # NextAuth configuration
│   ├── db.ts                    # Re-export of db/index.ts (convenience alias)
│   ├── errors.ts                # Typed error classes (AppError, NotFoundError, etc.)
│   ├── utils.ts                 # Pure utility functions (cn, formatDate, slugify)
│   └── validators/              # Zod schemas (one per domain)
│       ├── user.ts
│       └── task.ts
├── scripts/
│   ├── migrate.ts               # Run migrations
│   ├── seed.ts                  # Run seeds
│   └── reset-db.ts              # Drop + recreate (dev only)
├── public/
│   └── images/
├── .env.local                   # Never committed. DATABASE_URL, NEXTAUTH_SECRET, etc.
├── CLAUDE.md                    # This file
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### Rules

1. **Route groups `(auth)` and `(dashboard)` are mandatory.** They separate layouts without affecting URLs. Every page belongs to exactly one group.
2. **`components/ui/` has zero business logic.** If a component references a database table, a user role, or a domain concept, it goes in `components/features/`.
3. **`lib/` is pure.** No React imports. No Next.js imports. `lib/` functions are testable in isolation.
4. **`db/index.ts` exports ONE connection.** Never create connections inside route handlers. The singleton is created at module load and reused.
5. **Zod schemas in `lib/validators/` are the source of truth.** TypeScript types are derived via `z.infer<typeof>`. Never define a type manually that a Zod schema can define.

---

## Database & SQLite Conventions

### Connection

```typescript
// db/index.ts
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = process.env.DATABASE_URL || path.join(process.cwd(), "data", "app.db");

const db = new Database(DB_PATH, {
  verbose: process.env.NODE_ENV === "development" ? console.log : undefined,
});

// SQLite pragmas — set once at startup
db.pragma("journal_mode = WAL");        // Write-Ahead Logging: concurrent reads during writes
db.pragma("foreign_keys = ON");          // Enforce FK constraints (off by default in SQLite)
db.pragma("busy_timeout = 5000");        // Wait 5s on lock instead of failing immediately
db.pragma("synchronous = NORMAL");       // WAL mode + NORMAL = safe and fast

export default db;
```

**Why these pragmas:**
- `WAL` — the single most important SQLite optimization. Without it, readers block writers.
- `foreign_keys = ON` — SQLite has FK support but it's off by default. We always want it.
- `busy_timeout` — prevents "database is locked" errors under concurrent access.
- `synchronous = NORMAL` — with WAL, NORMAL is durable and 2x faster than FULL.

### Migrations

Migrations live in `db/migrations/` as plain `.sql` files:

```
db/migrations/
  001_create_users.sql
  002_create_tasks.sql
  003_add_user_avatar.sql
```

**Naming:** `NNN_description.sql` — three-digit prefix, snake_case description.

**Content rules:**
- Each file is one atomic migration. Wrap in a transaction if doing multiple statements.
- `CREATE TABLE IF NOT EXISTS` for new tables.
- `ALTER TABLE ... ADD COLUMN` for new columns. SQLite does not support `DROP COLUMN` or `ALTER COLUMN` — if you need these, create a new table and migrate data.
- Always include `NOT NULL` with a `DEFAULT` for new columns on existing tables.
- No `DROP TABLE` in migrations. Use `scripts/reset-db.ts` for that.

**Migration runner** (`scripts/migrate.ts`):
- Reads all `.sql` files from `db/migrations/` sorted by name.
- Tracks applied migrations in a `_migrations` table.
- Runs each unapplied migration in a transaction.
- Prints what was applied. Idempotent.

### Query Patterns

```typescript
// ✅ Prepared statements (faster on repeated calls)
const getUserById = db.prepare<[], User>("SELECT * FROM users WHERE id = ?");
const user = getUserById.get(userId);

// ✅ Insert with RETURNING
const insertUser = db.prepare(`
  INSERT INTO users (email, name, created_at)
  VALUES (?, ?, datetime('now'))
  RETURNING id, email, name, created_at
`);
const newUser = insertUser.get(email, name);

// ✅ Transactions (atomic multi-step operations)
const transferFunds = db.transaction((fromId: number, toId: number, amount: number) => {
  db.prepare("UPDATE accounts SET balance = balance - ? WHERE id = ?").run(amount, fromId);
  db.prepare("UPDATE accounts SET balance = balance + ? WHERE id = ?").run(amount, toId);
});
transferFunds(1, 2, 100);

// ✅ JSON aggregation (SQLite 3.38+)
const usersWithRoles = db.prepare(`
  SELECT u.*, json_group_array(r.name) as roles
  FROM users u
  LEFT JOIN user_roles ur ON ur.user_id = u.id
  LEFT JOIN roles r ON r.id = ur.role_id
  GROUP BY u.id
`).all();

// ❌ Never do this
const users = db.prepare("SELECT * FROM " + tableName).all();  // SQL injection
```

### Schema Design Rules

1. **Every table has `id INTEGER PRIMARY KEY`.** SQLite optimizes `INTEGER PRIMARY KEY` as the rowid — it's the fastest possible primary key.
2. **Timestamps are `TEXT` storing ISO 8601.** `datetime('now')` in SQLite produces ISO 8601. Parse with `new Date()` in TypeScript.
3. **Booleans are `INTEGER` (0/1).** SQLite has no native boolean. Use `CHECK (column IN (0, 1))` if you want enforcement.
4. **Enums are `TEXT` with `CHECK`.** `status TEXT CHECK (status IN ('active', 'inactive', 'banned')) NOT NULL DEFAULT 'active'`.
5. **Foreign keys reference `id` columns.** Always add `ON DELETE CASCADE` or `ON DELETE SET NULL` explicitly. Never rely on default behavior.
6. **Index columns used in `WHERE` and `JOIN`.** But don't over-index — each index slows writes. Index what you query.

---

## Server vs. Client Components

### Default: Server

Every component is a Server Component unless explicitly marked. This is the correct mental model.

```typescript
// ✅ Server Component (default) — can query DB directly
// app/(dashboard)/page.tsx
import db from "@/db";

export default async function DashboardPage() {
  const stats = db.prepare("SELECT COUNT(*) as total FROM users").get();
  return <StatsDisplay total={stats.total} />;
}
```

### When to use `"use client"`

Only when you need:
- `useState`, `useReducer`, `useEffect`
- Browser APIs (`window`, `localStorage`, `IntersectionObserver`)
- Event handlers (`onClick`, `onChange`, `onSubmit`)
- Third-party libraries that use hooks

```typescript
// ✅ Client Component — interactive form
"use client";

import { useState } from "react";

export function SearchInput({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState("");
  return (
    <input
      value={query}
      onChange={(e) => {
        setQuery(e.target.value);
        onSearch(e.target.value);
      }}
    />
  );
}
```

### The Boundary Rule

**Server Components can import Client Components. Client Components cannot import Server Components.** Pass server data as props to client components. Never fetch in a client component when a server component can do it.

```
✅ ServerComponent → renders → ClientComponent (passes data as props)
❌ ClientComponent → imports → ServerComponent (won't work)
```

---

## Data Validation (Zod)

Every piece of external input — form submissions, API payloads, URL params — goes through Zod.

```typescript
// lib/validators/user.ts
import { z } from "zod";

export const CreateUserSchema = z.object({
  email: z.string().email("Invalid email address"),
  name: z.string().min(1, "Name is required").max(100),
  role: z.enum(["admin", "member"]).default("member"),
});

export type CreateUserInput = z.infer<typeof CreateUserSchema>;

// In a Server Action:
export async function createUser(formData: FormData) {
  const parsed = CreateUserSchema.safeParse({
    email: formData.get("email"),
    name: formData.get("name"),
    role: formData.get("role"),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  // parsed.data is fully typed and validated
  db.prepare("INSERT INTO users (email, name, role) VALUES (?, ?, ?)").run(
    parsed.data.email,
    parsed.data.name,
    parsed.data.role
  );
}
```

**Rules:**
1. Zod schemas live in `lib/validators/`. One file per domain entity.
2. Types are derived: `type User = z.infer<typeof UserSchema>`. Never define both separately.
3. Validate at the boundary (Server Actions, API routes). Internal functions trust their inputs.
4. Return `{ error }` objects, never throw for validation errors. Throw for actual failures.

---

## API Routes

Use API routes only when Server Components can't handle it:
- Webhooks from external services
- Client-side mutations that need immediate response (no form submission)
- Streaming responses (SSE, WebSocket upgrade)

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import Stripe from "stripe";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = headers().get("stripe-signature")!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed":
      // handle
      break;
  }

  return NextResponse.json({ received: true });
}
```

**Rules:**
1. Every API route returns JSON. No server-rendered HTML from API routes.
2. Validate input with Zod before processing.
3. Return appropriate HTTP status codes: 200 success, 201 created, 400 bad input, 401 unauthorized, 404 not found, 500 server error.
4. Never expose internal error details in production. Log them, return generic messages.

---

## Error Handling

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export class NotFoundError extends AppError {
  constructor(entity: string, id: string | number) {
    super(`${entity} #${id} not found`, "NOT_FOUND", 404);
  }
}

export class ValidationError extends AppError {
  constructor(public readonly fields: Record<string, string[]>) {
    super("Validation failed", "VALIDATION_ERROR", 400);
  }
}
```

**Rules:**
1. Use `AppError` subclasses for expected failures. These are safe to show to users.
2. Unexpected errors (DB failures, network errors) are logged server-side; users see a generic message.
3. In Server Components, use `error.tsx` boundary files. In Server Actions, return `{ error: string }`.
4. Never `try/catch` without logging. Silent failures are bugs.

---

## Auth & Authorization

```typescript
// lib/auth.ts
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import db from "@/db";
import { verifyPassword } from "@/lib/password";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      async authorize({ email, password }) {
        const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email);
        if (!user || !(await verifyPassword(password, user.password_hash))) return null;
        return { id: user.id, email: user.email, name: user.name, role: user.role };
      },
    }),
  ],
  callbacks: {
    authorized: ({ auth }) => !!auth, // middleware protection
  },
});
```

**Rules:**
1. Check auth in middleware (`middleware.ts` uses `auth()` callback). Routes inside `(dashboard)` are protected by default.
2. For Server Actions, call `auth()` at the top. If null, return `{ error: "Unauthorized" }`.
3. Never trust client-side auth state. Always verify server-side.
4. Roles are strings in the `users.role` column. Use `auth().user.role` to check permissions.

---

## Styling (Tailwind)

```tsx
// ✅ Use the cn() utility for conditional classes
import { cn } from "@/lib/utils";

<button
  className={cn(
    "px-4 py-2 rounded-lg font-medium transition-colors",
    variant === "primary" && "bg-blue-600 text-white hover:bg-blue-700",
    variant === "secondary" && "bg-gray-200 text-gray-900 hover:bg-gray-300",
    disabled && "opacity-50 cursor-not-allowed",
  )}
>
  {children}
</button>
```

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Rules:**
1. `cn()` is the only way to compose classes. Never template-literal Tailwind classes.
2. Colors use the Tailwind palette. No custom hex values in components — define them in `tailwind.config.ts` if needed.
3. Responsive: `sm:` (640px), `md:` (768px), `lg:` (1024px). Mobile-first (no prefix = mobile).
4. Dark mode via `dark:` prefix. Store preference in cookie, not localStorage (so SSR can read it).

---

## Dev Commands

```bash
# Development
pnpm dev                        # Start dev server (localhost:3000)

# Database
pnpm db:migrate                 # Run pending migrations
pnpm db:seed                    # Seed dev data
pnpm db:reset                   # Drop + recreate + migrate + seed (dev only!)

# Testing
pnpm test                       # Run all tests
pnpm test -- --watch            # Watch mode
pnpm test -- --coverage         # Coverage report

# Build & Deploy
pnpm build                      # Production build
pnpm start                      # Start production server

# Code Quality
pnpm lint                       # ESLint
pnpm typecheck                  # tsc --noEmit
pnpm format                     # Prettier
```

---

## Anti-Patterns (Don't Do These)

| ❌ Anti-Pattern | ✅ Do This Instead | Why |
|---|---|---|
| `"use client"` on every component | Remove the directive, use Server Components | Client components ship JS to the browser. Server components don't. |
| Fetching data in `useEffect` | Fetch in a Server Component, pass as props | Server fetches are faster (no waterfall, no loading state). |
| Using `any` | Use `unknown` + type guards | `any` disables the type checker. `unknown` forces you to check. |
| Inline SQL strings with concatenation | Use `?` parameterized queries | SQL injection. No exceptions. |
| Calling `new Database()` in every file | Import the singleton from `db/index.ts` | Multiple connections to SQLite = locking issues. |
| Putting business logic in components | Put it in `lib/` or Server Actions | Components render UI. Logic is testable and reusable. |
| Using `router.push()` for form submissions | Use Server Actions + `redirect()` | Server Actions work without JS. Progressive enhancement. |
| Catching errors and returning null | Use `error.tsx` boundaries or return `{ error }` | Silent failures are the worst bugs to debug. |
| Storing JWT in localStorage | Use httpOnly cookies via NextAuth | localStorage is vulnerable to XSS. Cookies are managed by the server. |
| One giant page component | Split into `page.tsx` + `loading.tsx` + `error.tsx` | Next.js convention. Each file handles its own lifecycle. |

---

## Testing

```typescript
// __tests__/validators/user.test.ts
import { describe, it, expect } from "vitest";
import { CreateUserSchema } from "@/lib/validators/user";

describe("CreateUserSchema", () => {
  it("accepts valid input", () => {
    const result = CreateUserSchema.safeParse({
      email: "test@example.com",
      name: "Alice",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid email", () => {
    const result = CreateUserSchema.safeParse({
      email: "not-an-email",
      name: "Alice",
    });
    expect(result.success).toBe(false);
  });

  it("defaults role to member", () => {
    const result = CreateUserSchema.parse({
      email: "test@example.com",
      name: "Alice",
    });
    expect(result.role).toBe("member");
  });
});
```

**Rules:**
1. Test Zod schemas, utility functions, and database queries. Don't test UI rendering.
2. Test files mirror source: `lib/validators/user.ts` → `__tests__/validators/user.test.ts`.
3. Use `:memory:` SQLite databases for tests. Never touch the real database.
4. Each test is independent. No shared state between tests.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Path to SQLite file (e.g., `./data/app.db`) |
| `NEXTAUTH_SECRET` | Yes | Random 32-byte hex string for session encryption |
| `NEXTAUTH_URL` | Yes (prod) | Canonical URL (e.g., `https://myapp.com`) |

**Rules:**
1. `.env.local` for local development. Never committed.
2. `.env.example` committed with placeholder values. Documents what's needed.
3. Access via `process.env.VARIABLE_NAME`. No runtime injection.
4. Secrets (API keys, passwords) only in `.env.local` or deployment secrets. Never in code.

---

## Git Conventions

**Branch naming:** `feat/short-description`, `fix/short-description`, `chore/short-description`

**Commit messages:** Conventional Commits format.
```
feat: add user avatar upload
fix: prevent duplicate email registration
chore: update dependencies
```

**PR checklist:**
- [ ] `pnpm typecheck` passes
- [ ] `pnpm lint` passes
- [ ] `pnpm test` passes
- [ ] Migration tested with fresh DB
- [ ] No `console.log` in production code
- [ ] New environment variables documented in `.env.example`
