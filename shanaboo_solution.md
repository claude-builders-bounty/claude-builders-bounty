  forbidden  1.  look at the issue, this is a template bounty. The user wants a `CLAUDE.md` file created for a Next.js + SQLite SaaS project. The repo currently only has `README.md` and `LICENSE`. I need to create a new file `CLAUDE.md` at the root. The diff should be for a new file.

The issue says:
- Covers: project structure, naming conventions, DB migration rules
- Includes: dev commands, patterns to follow, anti-patterns to avoid
- Opinionated — not generic. Every rule has a reason.
- Usable without modification on a greenfield Next.js + SQLite project
- Tested: create a new project, paste the CLAUDE.md, confirm Claude Code understands the context without asking clarifying questions

Expected Sections:
- Stack & versions
- Folder structure
- SQL / migration conventions
- Component patterns
- What we don't do (and why)

I need to create a comprehensive, opinionated CLAUDE.md. Since the repo is `claude-builders-bounty/claude-builders-bounty`, and the issue is about creating a template, the file should be created at the root. The file listing shows `README.md` and `LICENSE`. So the new file is `CLAUDE.md`.

I will write a detailed CLAUDE.md that meets all criteria. It should be production-ready and opinionated.

Let's draft the content:

```markdown
# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Next.js 15** (App Router, Server Components by default)
- **React 19** (Server Components first; client components only when needed)
- **TypeScript** (strict mode, no `any` without comment)
- **SQLite** via `better-sqlite3` (local) or **Turso** (cloud)
- **Drizzle ORM** (type-safe SQL, not Prisma — zero runtime bloat)
- **Tailwind CSS** (utility-first, no arbitrary values in markup)
- **Zod** (schema validation, shared between server and client)
- **next-safe-action** (type-safe server actions with input validation)

> **Why this stack?** Next.js 15 App Router eliminates API boilerplate. Drizzle keeps SQL visible and type-safe. SQLite keeps ops simple until you outgrow it. Zod + next-safe-action removes the need for a separate tRPC layer.

---

## Folder Structure

\`\`\`
src/
  app/                    # Next.js App Router
    (auth)/               # Route groups for layout isolation
      login/
      register/
    (dashboard)/
      dashboard/
        page.tsx
        layout.tsx
    api/                  # Only for webhooks or external API routes
    layout.tsx
    page.tsx
  components/
    ui/                   # shadcn/ui primitives (button, input, etc.)
    forms/                # Form-specific components (LoginForm, etc.)
    layout/               # Header, Sidebar, Footer
  lib/
    db/                   # Drizzle schema & connection
      schema.ts
      index.ts            # Database client singleton
    actions/              # next-safe-action server actions
      auth.ts
      billing.ts
    validations/          # Zod schemas
      auth.ts
    utils.ts              # cn(), formatters, etc.
  hooks/                  # Shared React hooks (useUser, etc.)
  types/                  # Global TypeScript types
\`\`\`

> **Why this structure?** Co-locating server actions in `lib/actions/` keeps them testable and discoverable. UI primitives stay separate from business logic. Route groups keep layouts clean.

---

## SQL / Migration Conventions

1. **Use Drizzle Kit for migrations.** Run `npx drizzle-kit generate` after every schema change. Commit `.sql` files.
2. **Schema in `src/lib/db/schema.ts` only.** No inline table definitions.
3. **Naming:**
   - Tables: plural, snake_case (`users`, `subscriptions`)
   - Columns: snake_case (`created_at`, `stripe_customer_id`)
   - Foreign keys: `table_id` referencing `table.id`
4. **Every table must have:**
   - `id: text("id").$defaultFn(() => createId())` — CUID, not auto-increment (avoids ID enumeration)
   - `created_at` and `updated_at` timestamps
5. **Soft deletes only.** Add `deleted_at` timestamp. Never `DELETE` a user row; filter with `.where(isNull(schema.users.deletedAt))`.
6. **Indexes:** Define in schema. Any query filtering on a column needs an index. Name them: `idx_table_column`.

> **Why?** Soft deletes prevent accidental data loss and simplify GDPR "right to be forgotten" (anonymize instead of hard delete). CUIDs prevent enumeration attacks and make DB sharding trivial later.

---

## Component Patterns

### Server Components (default)

Fetch data directly in the component. Pass primitives to children.

\`\`\`tsx
// app/dashboard/page.tsx
import { db } from "@/lib/db";
import { DashboardClient } from "./DashboardClient";

export default async function DashboardPage() {
  const user = await db.query.users.findFirst(); // Drizzle
  if (!user) return <div>Not logged in</div>;
  return <DashboardClient initialData={user} />;
}
\`\`\`

### Client Components

Only when using `useState`, `useEffect`, or browser APIs. Mark explicitly:

\`\`\`tsx
"use client";

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
\`\`\`

### Forms

Always use `next-safe-action` with Zod.

\`\`\`tsx
// lib/actions/auth.ts
"use server";

import { actionClient } from "@/lib/safe-action";
import { z } from "zod";

export const login = actionClient
  .schema(z.object({ email: z.string().email(), password: z.string().min(8) }))
  .action(async ({ parsedInput }) => {
    // ... auth logic
  });
\`\`\`

---

## Dev Commands

\`\`\`bash
# Install
pnpm install

# Dev server
pnpm dev

# Generate & run migrations
pnpm db:generate
pnpm db:migrate

# Type check & lint (run before every commit)
pnpm typecheck
pnpm lint
pnpm format
\`\`\`

---

## Anti-Patterns (What We Don't Do)

| Anti-Pattern | Why | What We Do Instead |
|--------------|-----|--------------------|
| \`"use client"\` at the top of every file | Defeats Server Components; ships more JS to client | Keep server components default; use client components only for interactivity |
| Storing secrets in \`.env.local\` only | Easy to leak; no shared config | Use \`.env.example\` + 1Password/