# CLAUDE.md — Next.js 15 + SQLite SaaS Project Instructions

> Opinionated, battle-tested standards and conventions for this Next.js 15 App Router + SQLite (Drizzle ORM / better-sqlite3 / Turso) SaaS application.

---

## 1. Tech Stack & Target Versions

| Layer | Tooling & Version | Notes |
|---|---|---|
| **Framework** | Next.js 15.x (App Router) | React 19, Server Components by default |
| **Language** | TypeScript 5.x (Strict) | No `any`, explicit return types on server actions |
| **Database** | SQLite / libSQL (better-sqlite3 local, Turso production) | Embedded WAL mode locally |
| **ORM & Migrations** | Drizzle ORM + `drizzle-kit` | Typed schema, strict migration files |
| **Styling** | Tailwind CSS v4 / PostCSS | Token-based theming with Dark mode support |
| **Auth** | Lucia / Auth.js / Better Auth (Session Cookies) | HTTP-only, SameSite=Lax |
| **Validation** | Zod v3.x | Parse all input at Server Action / Route boundaries |
| **Testing** | Vitest + React Testing Library | Fast unit & integration tests |

---

## 2. Directory & Architecture Structure

```text
├── src/
│   ├── app/                    # Next.js App Router routes & pages
│   │   ├── (auth)/             # Route group: login, signup, reset-password
│   │   ├── (dashboard)/        # Route group: user app, billing, settings
│   │   ├── api/                # Webhook & external integrations only
│   │   ├── layout.tsx          # Root layout with font and theme providers
│   │   ├── globals.css         # Tailwind utility classes and CSS variables
│   │   └── error.tsx           # Global error boundary
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Headless primitives (Button, Modal, Input)
│   │   ├── forms/              # Form components with validation
│   │   └── layout/             # Header, Sidebar, Nav, Footer
│   ├── db/                     # Database layer
│   │   ├── schema/             # Drizzle table definitions (*.ts)
│   │   │   ├── users.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── index.ts        # Schema aggregator export
│   │   ├── migrations/         # Generated SQL migration files (0000_*.sql)
│   │   ├── index.ts            # Database client instance (WAL mode config)
│   │   └── migrate.ts          # Migration runner script
│   ├── lib/                    # Shared business logic & server actions
│   │   ├── actions/            # "use server" mutation handlers
│   │   ├── auth/               # Session creation, hashing, cookie helpers
│   │   ├── stripe/             # Stripe billing & webhook processors
│   │   └── utils.ts            # Pure helper utilities
│   └── types/                  # Shared TypeScript interfaces & types
├── drizzle.config.ts           # Drizzle migration config
└── vitest.config.ts            # Test runner config
```

---

## 3. SQL & SQLite Migration Rules

1. **WAL Mode is Mandatory**:
   - `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL;` must be set on database initialization to ensure high concurrency without lock contention.
2. **Foreign Keys Enforcement**:
   - Always run `PRAGMA foreign_keys = ON;` upon connection opening.
3. **No Direct SQL Execution in Components**:
   - All database reads occur inside React Server Components (`RSC`) or dedicated data-access layer (`src/lib/data/`).
   - All mutations occur exclusively via **Server Actions** (`"use server"`).
4. **Strict Drizzle Migrations**:
   - Run `pnpm drizzle-kit generate` followed by `pnpm db:migrate`.
   - Never manually modify generated SQL files in `src/db/migrations/`.
   - Use timestamps and UUID / `nanoid` primary keys for distributed readiness.
5. **No Long-Running Transactions**:
   - SQLite table locks during writes. Keep write transactions small, focused, and under 50ms.

---

## 4. Component & Server Action Patterns

### Server Action Template (`src/lib/actions/*.ts`)
```typescript
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";
import { db } from "@/db";
import { users } from "@/db/schema";
import { requireAuth } from "@/lib/auth";

const UpdateProfileSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
});

export type ActionState = {
  success: boolean;
  message?: string;
  errors?: Record<string, string[]>;
};

export async function updateProfile(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const session = await requireAuth();
  const rawData = Object.fromEntries(formData.entries());
  const validated = UpdateProfileSchema.safeParse(rawData);

  if (!validated.success) {
    return {
      success: false,
      errors: validated.error.flatten().fieldErrors,
    };
  }

  await db
    .update(users)
    .set({ name: validated.data.name, updatedAt: new Date() })
    .where(eq(users.id, session.user.id));

  revalidatePath("/dashboard/settings");
  return { success: true, message: "Profile updated successfully." };
}
```

### Server vs. Client Component Rules
- **Default to Server Components**: Keep data fetching, secrets, and heavy dependencies on the server.
- **Isolate Client Components**: Add `"use client"` only at leaf interactive nodes (buttons, dropdowns, forms with client state).
- **No Prop Drilling Server Data**: Pass simple serializable props; do not pass database instances or server-only objects to client components.

---

## 5. Development & CI Commands

```bash
# Development
pnpm dev             # Start Next.js local server (Turbopack)
pnpm build           # Build optimized production bundle
pnpm start           # Run production server

# Database & Migrations
pnpm db:generate     # Generate new Drizzle migration from schema changes
pnpm db:migrate      # Apply pending migrations to SQLite database
pnpm db:studio       # Launch Drizzle Studio DB viewer GUI

# Code Quality & Tests
pnpm lint            # ESLint check
pnpm typecheck       # Run `tsc --noEmit`
pnpm test            # Run Vitest test suite
pnpm test:coverage   # Vitest with coverage report
```

---

## 6. What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It | Preferred Alternative |
|---|---|---|
| **No API Route Handlers for internal CRUD** | Adds redundant HTTP overhead, serialization, and typing boilerplate in App Router. | Use **Server Actions** directly. |
| **No `useEffect` for data fetching** | Causes waterfalls, client state desync, and SEO layout shifts. | Fetch directly in **Server Components**. |
| **No Unindexed Foreign Keys** | SQLite does not automatically index foreign keys; joins degrade to full table scans. | Explicitly define `.index()` on foreign key columns in Drizzle schema. |
| **No Raw `any` Type Casts** | Breaks TypeScript type safety guarantees and hides runtime shape mismatches. | Use **Zod schemas** or `unknown` with type predicates. |
| **No Client-side Secrets** | Leaks API keys (Stripe secret key, auth secrets) to browser. | Never prefix private environment variables with `NEXT_PUBLIC_`. |
