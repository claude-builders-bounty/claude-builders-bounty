# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Architecture

This repository is a production SaaS application built with **Next.js 15 App Router**, **React 19**, **TypeScript**, and **SQLite** (via Turso / `better-sqlite3` and Drizzle ORM).

Claude Code must strictly adhere to the conventions, directory invariants, database policies, and architectural boundaries specified below.

---

## 1. Stack & Core Versions

- **Framework:** Next.js 15 (App Router, Server Actions, Turbopack)
- **Runtime:** Node.js 20+ / React 19
- **Language:** TypeScript 5.6+ (Strict mode: `noImplicitAny: true`, `exactOptionalPropertyTypes: true`)
- **Database:** SQLite (Local development: `better-sqlite3` | Edge / Distributed production: `@libsql/client` via Turso)
- **ORM & Migrations:** Drizzle ORM (`drizzle-orm` ^0.35.0, `drizzle-kit` ^0.26.0)
- **Validation:** Zod 3.23+ (Strict boundary input parsing)
- **Styling:** Tailwind CSS v4 with modern CSS variables (HSL tokens, system dark mode support)
- **Testing:** Vitest + React Testing Library

---

## 2. Directory & File Organization

Enforce clean domain boundaries. Code must live in its designated architectural layer:

```text
├── app/                        # Next.js App Router (Routing, Layouts, Metadata)
│   ├── (auth)/                 # Auth route group (login, register, forgot-password)
│   ├── (dashboard)/            # Authenticated application workspace
│   │   ├── dashboard/          # Main dashboard view
│   │   ├── settings/           # Account & billing settings
│   │   └── layout.tsx          # Authenticated layout with sidebar & user nav
│   ├── api/                    # Route handlers ONLY for external webhooks (Stripe, etc.)
│   ├── error.tsx               # Root error boundary
│   ├── not-found.tsx           # 404 handler
│   └── layout.tsx              # Root HTML wrapper and font injection
├── actions/                    # Next.js Server Actions (Mutations & business workflows)
│   ├── auth.ts                 # Sign in, sign up, session revocation actions
│   └── billing.ts              # Customer portal & checkout actions
├── components/                 # React components
│   ├── ui/                     # Reusable primitive design system components (Button, Dialog)
│   └── features/               # Domain-specific composed widgets (WorkspaceCard, InvoiceList)
├── db/                         # Database layer
│   ├── schema/                 # Drizzle table definitions (modular per domain)
│   │   ├── users.ts
│   │   ├── organizations.ts
│   │   └── index.ts            # Master schema export
│   ├── migrations/             # Generated versioned SQL migrations (DO NOT edit manually)
│   ├── client.ts               # Database client singleton with PRAGMA enforcement
│   └── seed.ts                 # Deterministic local seed script
├── lib/                        # Shared infrastructure utilities
│   ├── auth.ts                 # Session verification & token hashing
│   ├── env.ts                  # Type-safe environment variable assertions via Zod
│   └── utils.ts                # Pure formatting and CSS class mergers (`cn`)
└── types/                      # Shared global TypeScript definitions
```

---

## 3. SQLite & Migration Conventions

SQLite is lightweight, embedded, and blindingly fast, but requires strict relational hygiene:

1. **Connection Pragma Enforcement:**
   Every SQLite connection MUST initialize foreign key enforcement and Write-Ahead Logging (WAL):
   ```typescript
   // db/client.ts
   sqlite.pragma('foreign_keys = ON;');
   sqlite.pragma('journal_mode = WAL;');
   sqlite.pragma('synchronous = NORMAL;');
   ```
2. **Primary Key Standard:**
   - **Never** use auto-incrementing integers for public SaaS entities (prevents enumeration attacks).
   - Use prefixed URL-safe NanoIDs or UUIDv7:
     - `usr_01H...` for users
     - `org_01H...` for organizations
     - `inv_01H...` for invoices
3. **Column Naming & Types:**
   - Database columns: `snake_case` (e.g., `created_at`, `org_id`).
   - TypeScript fields: `camelCase` mapped via Drizzle decorators.
   - Timestamps: Store as `INTEGER` representing Unix epoch milliseconds (`{ mode: 'timestamp_ms' }`).
   - Booleans: Store as `INTEGER` (`0` or `1`, `{ mode: 'boolean' }`).
4. **Index Foreign Keys:**
   - SQLite does **not** automatically index foreign keys. You must explicitly create an index on every foreign key column (`user_id`, `org_id`) to prevent full-table scans during JOIN operations.
5. **Atomic Transactions:**
   - Any business operation that alters more than one table MUST be wrapped in `db.transaction(async (tx) => { ... })`.
6. **Zero Drift Migration Policy:**
   - Never run raw `ALTER TABLE` manually against a database.
   - Always edit `db/schema/*.ts` -> run `npm run db:generate` -> inspect SQL diff -> run `npm run db:migrate`.

---

## 4. Component & Server Action Patterns

1. **Server Components First:**
   - Every component in `app/` is a **Server Component** by default.
   - Fetch data directly from SQLite in Server Components:
     ```typescript
     // app/(dashboard)/dashboard/page.tsx
     import { db } from "@/db/client";
     import { users } from "@/db/schema";
     
     export default async function DashboardPage() {
       const userList = await db.select().from(users);
       return <UserTable data={userList} />;
     }
     ```
2. **Client Component Boundary:**
   - Add `'use client'` strictly to interactive leaves (e.g., modal triggers, form inputs, toggle buttons).
   - Never wrap entire pages in `'use client'`.
3. **Server Action Mutation Pattern:**
   - Server Actions must validate inputs at runtime using Zod.
   - Return structured status objects rather than throwing unhandled exceptions:
     ```typescript
     // actions/workspace.ts
     'use server';
     import { z } from "zod";
     import { auth } from "@/lib/auth";
     
     const CreateWorkspaceSchema = z.object({
       name: z.string().min(2).max(50),
     });
     
     export type ActionState = {
       success: boolean;
       error?: string;
       data?: unknown;
     };
     
     export async function createWorkspaceAction(formData: FormData): Promise<ActionState> {
       const session = await auth();
       if (!session?.user) return { success: false, error: "Unauthorized" };
     
       const parsed = CreateWorkspaceSchema.safeParse({ name: formData.get("name") });
       if (!parsed.success) return { success: false, error: parsed.error.issues[0].message };
     
       // DB execution...
       return { success: true };
     }
     ```
4. **Named Exports Only:**
   - Use named exports (`export function UserCard()`) for components. Avoid `export default` outside of Next.js file-system conventions (`page.tsx`, `layout.tsx`, `error.tsx`).

---

## 5. What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It |
| :--- | :--- |
| **❌ Internal API Routes (`app/api/data`)** | Server Components execute directly on the server next to SQLite. Adding an internal HTTP API route introduces unnecessary network hops, JSON serialization overhead, and latency. |
| **❌ `useEffect` for Data Fetching** | Causes client-side waterfalls, layout shifts, and flash-of-unauthenticated-content. Fetch in Server Components. |
| **❌ Raw SQL String Concatenation** | Vulnerable to SQL injection. Always use Drizzle query builders or parameterized prepared statements (`sql\`SELECT * FROM users WHERE id = ${id}\``). |
| **❌ Client-Side Database Connections** | SQLite files exist exclusively on the server filesystem. Any client import of `db/client.ts` will break bundling and leak server secrets. |
| **❌ Unbounded Queries** | Every query returning a list MUST include `.limit()` and `.offset()` pagination to prevent memory exhaustion as tables grow. |
| **❌ Auto-Increment Sequential IDs** | Predictable IDs allow competitors to scrape customer counts or access endpoints via enumeration. |

---

## 6. Daily Development Commands

```bash
# Development server (runs on http://localhost:3000)
npm run dev

# Production build validation (typecheck + bundle)
npm run build

# Database schema management
npm run db:generate   # Scans schema/ and generates migrations in db/migrations/
npm run db:migrate    # Executes pending SQL migrations on the SQLite database
npm run db:studio     # Launches Drizzle Studio GUI for visual table inspection
npm run db:seed       # Populates local SQLite database with test accounts

# Quality & Test Gates
npm run lint          # Next.js ESLint validation
npm run test          # Vitest unit & integration test runner
```
