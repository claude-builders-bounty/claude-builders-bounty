# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Framework:** Next.js 15 (App Router only, no Pages Router)
- **Runtime:** Node.js 20 LTS
- **Language:** TypeScript 5.x, strict mode (`"strict": true`)
- **Database:** SQLite via `better-sqlite3` (dev/self-hosted) or Turso/libSQL (production)
- **ORM:** Drizzle ORM (type-safe, SQL-first)
- **Styling:** Tailwind CSS 4
- **Auth:** Lucia Auth v3 (session-based, SQLite adapter)
- **Validation:** Zod (shared schemas between client/server)
- **Testing:** Vitest (unit) + Playwright (e2e)
- **Package Manager:** pnpm

## Dev Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm db:push      # Push schema changes to SQLite
pnpm db:migrate   # Run pending migrations
pnpm db:studio    # Open Drizzle Studio (DB browser)
pnpm test         # Run Vitest
pnpm test:e2e     # Run Playwright
pnpm lint         # ESLint + type-check
pnpm format       # Prettier
```

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth routes (login, register, forgot-password)
│   ├── (dashboard)/        # Protected routes (requires session)
│   ├── api/                # Route handlers (REST-style)
│   │   └── [resource]/route.ts
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Primitives (Button, Input, Card) — no business logic
│   └── [feature]/          # Feature-specific components
├── db/
│   ├── schema.ts           # Drizzle schema (single source of truth)
│   ├── migrations/         # Generated SQL migrations (never hand-edit)
│   ├── index.ts            # DB connection singleton
│   └── queries/            # Reusable query functions
│       └── [resource].ts   # e.g., users.ts, projects.ts
├── lib/
│   ├── auth.ts             # Lucia config + helpers
│   ├── validations/        # Zod schemas (shared client/server)
│   └── utils.ts            # Pure utility functions
├── hooks/                  # React hooks
└── types/                  # Global TypeScript types
```

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files/folders | kebab-case | `user-profile.tsx` |
| Components | PascalCase | `UserProfile` |
| Functions | camelCase | `getUserById` |
| DB tables | snake_case (plural) | `user_sessions` |
| DB columns | snake_case | `created_at` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |
| Route handlers | `route.ts` | `app/api/users/route.ts` |
| Server Actions | `actions.ts` | `app/(dashboard)/actions.ts` |

## SQL / Migration Conventions

1. **Schema is the source of truth.** Define tables in `db/schema.ts` using Drizzle's TypeScript API.
2. **Generate migrations, never write them.** Run `pnpm db:generate` → commit the SQL file.
3. **Never hand-edit generated migrations.** If wrong, delete and regenerate.
4. **Migrations are additive.** Never drop columns in production. Add new columns as nullable, backfill, then make non-null in a later migration.
5. **Every table has:** `id` (text, nanoid), `created_at` (integer, unix ms), `updated_at` (integer, unix ms).
6. **Use transactions** for multi-table writes: `db.transaction(async (tx) => { ... })`.
7. **Indexes:** Add indexes for any column used in WHERE or JOIN. Name them `idx_[table]_[column]`.
8. **Tenant scoping:** Every query for user data MUST include `WHERE tenant_id = ?`. No exceptions.
9. **Soft delete preferred:** Add `deleted_at` column instead of DELETE. Reason: audit trail + undo.
10. **No raw SQL strings.** Use Drizzle's query builder. Reason: type safety + injection prevention.

## Component Patterns

### Server Components (default)
```tsx
// app/(dashboard)/projects/page.tsx
import { getProjects } from "@/db/queries/projects";

export default async function ProjectsPage() {
  const projects = await getProjects();
  return <ProjectList projects={projects} />;
}
```

### Client Components (only when needed)
```tsx
// components/project/project-form.tsx
"use client";
import { useForm } from "react-hook-form";
// Only use "use client" for: event handlers, useState, useEffect, browser APIs
```

### Rules
- **Default to Server Components.** Reason: smaller bundle, direct DB access, no waterfall.
- **"use client" only for interactivity.** If it doesn't need useState/useEffect/onClick, it's a Server Component.
- **No `useEffect` for data fetching.** Use Server Components or Route Handlers instead.
- **Props over context.** Pass data down explicitly. Context = hidden dependencies.
- **Collocate.** Component + its types + its tests in the same folder.

## Validation

- **One Zod schema per resource** in `lib/validations/[resource].ts`.
- **Share between client and server.** Import the same schema in forms and route handlers.
- **Parse, don't validate.** Use `schema.parse(data)` — throws on invalid, returns typed data.
- **Never trust client input.** Always validate in route handlers/server actions, even if client validates too.

## Auth

- **Session-based** via Lucia. No JWTs. Reason: revocable, no token refresh complexity.
- **Middleware** checks session on every `(dashboard)` route.
- **CSRF protection** via Lucia's built-in origin check.
- **Password hashing** with Argon2id (via `@node-rs/argon2`).

## Error Handling

- **Route handlers:** Return `NextResponse.json({ error: "message" }, { status: 4xx })`.
- **Server Actions:** Return `{ success: false, error: "message" }` — never throw to the client.
- **DB errors:** Catch and map to user-friendly messages. Never expose raw SQL errors.
- **404s:** Use `notFound()` from `next/navigation`.

## Security

- **Input validation** on every endpoint (Zod).
- **Parameterized queries** only (Drizzle handles this).
- **Rate limiting** on auth endpoints (login, register, forgot-password).
- **CORS:** Disabled by default. Only enable for specific API routes if needed.
- **Environment variables:** Never commit `.env`. Use `.env.example` as template.
- **Dependencies:** Pin exact versions. Audit weekly with `pnpm audit`.

## Testing

- **Unit tests:** `*.test.ts` next to the file they test. Test pure functions and DB queries.
- **E2E tests:** `tests/e2e/*.spec.ts`. Test critical user flows (signup → create → delete).
- **Test DB:** Use in-memory SQLite (`:memory:`) for unit tests. Fresh DB per test file.
- **No mocks for DB.** Use real SQLite. It's fast enough. Reason: mocks drift from reality.

## What We Don't Do (and Why)

| Anti-pattern | Why we avoid it |
|-------------|----------------|
| Pages Router | App Router is the future. No mixing. |
| `getServerSideProps` | App Router uses async Server Components instead. |
| JWT auth | Sessions are simpler, revocable, and don't need refresh logic. |
| Prisma | Drizzle is faster, lighter, and more SQL-transparent for SQLite. |
| `useEffect` for fetching | Creates waterfalls. Server Components fetch at render time. |
| Global state (Redux/Zustand) | Server Components + props eliminate most client state needs. |
| `any` type | Use `unknown` + type narrowing. `any` defeats TypeScript's purpose. |
| Barrel exports (`index.ts`) | Breaks tree-shaking and makes imports ambiguous. |
| Relative imports beyond 2 levels | Use `@/` path alias. `../../../` is unreadable. |
| Hand-written SQL migrations | Drift from schema. Generate from Drizzle schema instead. |
| ORM `.findMany()` without limit | Always paginate. Unbounded queries kill performance at scale. |
| Storing secrets in code | Use environment variables. Rotate on exposure. |

## PR Workflow

1. Branch from `main`: `feat/[short-description]` or `fix/[short-description]`
2. Commit messages: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
3. PR must pass: `pnpm lint` + `pnpm test` + `pnpm build`
4. Squash merge to `main`. One commit per feature.
5. Delete branch after merge.
