# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

This document defines architecture standards, development conventions, database rules, and coding patterns for this codebase. Claude Code must follow these directives strictly when reading, generating, or refactoring code.

---

## 1. Stack & Pinned Versions

- **Framework**: Next.js 15 (App Router, async request APIs)
- **UI & Runtime**: React 19 (`useActionState`, Server Components by default)
- **Language**: TypeScript 5.6+ (`strict: true`, `noImplicitAny: true`)
- **Styling**: Tailwind CSS v4 (`@tailwindcss/postcss`) + `shadcn/ui` (Radix UI primitives)
- **Database & ORM**: SQLite (`@libsql/client` for Turso / serverless edge, or `better-sqlite3` for local node runtime) + Drizzle ORM (`drizzle-orm` ^0.36.0, `drizzle-kit` ^0.28.0)
- **Validation**: Zod 3.23+ for runtime schema validation
- **Icons**: `lucide-react`
- **Package Manager**: `pnpm` (required, do not use `npm` or `yarn`)

---

## 2. Development Commands

```bash
# Development & Build
pnpm dev              # Start local dev server on http://localhost:3000
pnpm build            # Production build with static typechecking
pnpm start            # Start production server
pnpm lint             # Run ESLint (Next.js core-web-vitals)
pnpm typecheck        # Run tsc --noEmit

# Database & Migrations (Drizzle ORM)
pnpm db:generate      # Generate SQL migration files from drizzle schema changes
pnpm db:migrate       # Apply pending migrations to SQLite database
pnpm db:push          # Push schema changes directly (prototyping only)
pnpm db:studio        # Open Drizzle Studio UI to inspect SQLite data
pnpm db:seed          # Seed database with mock data

# Testing
pnpm test             # Run test suite (Vitest)
pnpm test:watch       # Run Vitest in interactive watch mode
```

---

## 3. Project Folder Structure

```
├── app/
│   ├── (auth)/                 # Auth route group (login, register, forgot-password)
│   ├── (dashboard)/            # Authenticated application shell
│   │   ├── layout.tsx          # Dashboard sidebar & top navigation (Server Component)
│   │   ├── page.tsx            # Main dashboard overview
│   │   └── settings/           # User & workspace settings
│   ├── api/                    # Route handlers for webhooks & public APIs
│   │   └── webhooks/stripe/    # Stripe webhook handler (verify signature with raw body)
│   ├── favicon.ico
│   ├── globals.css             # Tailwind v4 theme variables
│   └── layout.tsx              # Root HTML wrapper, fonts, providers
├── components/
│   ├── ui/                     # shadcn/ui primitive components (Button, Input, Dialog)
│   ├── forms/                  # Interactive form components ("use client")
│   └── shared/                 # Reusable domain components (UserAvatar, EmptyState)
├── db/
│   ├── index.ts                # Database client initialization with WAL & Foreign Keys
│   ├── schema/                 # Drizzle schema definitions (split by domain)
│   │   ├── index.ts            # Central export of all tables & relations
│   │   ├── users.ts            # Users, sessions, accounts
│   │   └── organizations.ts    # Workspaces, memberships, billing
│   └── migrations/             # Generated SQL migration files (tracked in git)
├── lib/
│   ├── actions/                # Server Actions (split by domain, e.g., user-actions.ts)
│   ├── queries/                # Read-only database query helper functions
│   ├── validations/            # Zod schemas shared between client forms & server actions
│   ├── auth.ts                 # Session verification & authentication helpers
│   └── utils.ts                # cn() class merging and generic utilities
├── public/                     # Static assets (SVGs, images)
├── drizzle.config.ts           # Drizzle Kit CLI configuration
└── tsconfig.json
```

---

## 4. SQL & SQLite Database Conventions

### Pragmas & Client Initialization
Every SQLite connection must explicitly enable foreign keys and write-ahead logging (WAL):
```typescript
// db/index.ts
import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import * as schema from './schema';

export const client = createClient({
  url: process.env.DATABASE_URL || 'file:local.db',
  authToken: process.env.DATABASE_AUTH_TOKEN,
});

// SQLite safety pragmas
client.execute('PRAGMA foreign_keys = ON;');
client.execute('PRAGMA journal_mode = WAL;');

export const db = drizzle(client, { schema });
```

### Table Definitions & Rules
1. **Primary Keys**: Use string-based ULIDs or prefixed nanoids (e.g., `usr_01H...`, `org_01H...`), NEVER auto-incrementing integers. This prevents enumeration attacks and allows client-side ID generation.
2. **Timestamps**: Store timestamps as Unix integer epoch milliseconds (`integer('created_at', { mode: 'timestamp_ms' })`) or ISO strings.
3. **Foreign Keys**: Always specify `onDelete: 'cascade'` or `onDelete: 'restrict'` explicitly on references.
4. **Indexes**: Add explicit indexes on all foreign key columns and frequently filtered columns (`status`, `slug`, `email`).
5. **Migrations**:
   - Always run `pnpm db:generate` to produce reviewable SQL files in `db/migrations/`.
   - Never edit existing, already-applied migration files; always create a new incremental migration.

---

## 5. Component & Data Flow Patterns

### Server Components by Default
- Data fetching belongs in Server Components. Fetch directly from queries (`lib/queries/*.ts`) or Drizzle queries.
- Never wrap a page with `"use client"` just to handle one button click. Push client interactivity down to leaf components:
```tsx
// app/(dashboard)/page.tsx (Server Component)
import { getOrganizationProjects } from '@/lib/queries/projects';
import { CreateProjectModal } from '@/components/forms/create-project-modal';

export default async function DashboardPage() {
  const projects = await getOrganizationProjects();
  return (
    <main className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <CreateProjectModal /> {/* Client Component at leaf */}
      </div>
      <ProjectList projects={projects} />
    </main>
  );
}
```

### Server Actions Architecture
- Every mutation must be a Server Action in `lib/actions/*.ts` with `"use server"`.
- Server Actions must return a standardized, strongly typed `ActionResponse<T>`:
```typescript
// types/action.ts
export type ActionResponse<T = void> = 
  | { success: true; data: T }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };
```
- Every Server Action must validate inputs with Zod before touching the database:
```typescript
// lib/actions/project-actions.ts
'use server';

import { db } from '@/db';
import { projects } from '@/db/schema';
import { createProjectSchema } from '@/lib/validations/project';
import { getRequiredUser } from '@/lib/auth';
import { revalidatePath } from 'next/cache';
import type { ActionResponse } from '@/types/action';

export async function createProjectAction(rawInput: unknown): Promise<ActionResponse<{ id: string }>> {
  const user = await getRequiredUser();
  const parsed = createProjectSchema.safeParse(rawInput);

  if (!parsed.success) {
    return {
      success: false,
      error: 'Invalid form input',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    const [created] = await db.insert(projects).values({
      ...parsed.data,
      userId: user.id,
    }).returning({ id: projects.id });

    revalidatePath('/dashboard');
    return { success: true, data: { id: created.id } };
  } catch (err) {
    return { success: false, error: 'Database operation failed' };
  }
}
```

---

## 6. Naming Conventions

- **Files & Directories**: `kebab-case` (e.g., `user-profile-card.tsx`, `create-project.ts`).
- **Components**: `PascalCase` (e.g., `ProjectTable`, `NotificationBadge`).
- **Functions & Hooks**: `camelCase` (e.g., `getWorkspaceUsers()`, `useDebounce()`).
- **Constants & Enums**: `UPPER_SNAKE_CASE` (e.g., `MAX_WORKSPACE_MEMBERS`, `DEFAULT_PAGE_SIZE`).
- **Database Tables**: Plural `snake_case` in SQLite (`users`, `workspace_members`).

---

## 7. What We DO NOT Do (and WHY)

1. **NO `useEffect` for data fetching**  
   *Why*: Causes client-side network waterfalls, layout shifts, and exposes API keys. Fetch data directly in Server Components using async/await.
2. **NO Prisma ORM**  
   *Why*: Prisma requires heavy Rust query engine binaries that bloat serverless cold starts. Drizzle compiles directly to lightweight SQL queries compatible with edge runtimes.
3. **NO raw database queries in Client Components**  
   *Why*: Leaks credentials and bypasses authorization. All DB interactions must execute in Server Components or Server Actions.
4. **NO unvalidated Server Actions**  
   *Why*: Server Actions are publicly exposed HTTP endpoints. Never trust input without `zod.safeParse()`.
5. **NO Default Exports (except Next.js pages/layouts)**  
   *Why*: Named exports ensure consistent symbol refactoring, auto-imports, and prevent naming mismatches across files.
6. **NO Barrel files (`index.ts` re-exporting entire directories)**  
   *Why*: Severely degrades Turbopack build performance and breaks tree-shaking in Next.js 15.
7. **NO auto-incrementing integer IDs (`id INTEGER PRIMARY KEY AUTOINCREMENT`)**  
   *Why*: Vulnerable to IDOR enumeration attacks and leaks business metric volume. Use ULIDs or nanoids.
