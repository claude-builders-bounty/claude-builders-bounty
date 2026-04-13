# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project context for Claude Code. Every rule has a reason.

## Stack & Versions

- **Framework:** Next.js 15 (App Router only — no Pages Router)
- **Runtime:** Node.js 20+
- **Language:** TypeScript 5.5+ (strict mode, no `any`)
- **Database:** SQLite via `better-sqlite3` (synchronous, single-process)
- **ORM:** None. Raw SQL with typed helpers. ORMs add abstraction we don't need for SQLite.
- **Styling:** Tailwind CSS 4. No CSS modules, no styled-components.
- **Auth:** `better-auth` or custom JWT in HTTP-only cookies. No next-auth — too much magic.
- **Package manager:** pnpm. Lock file is committed.
- **Deployment:** Single VPS with `pm2` or Docker. SQLite doesn't work on serverless (Vercel edge).

## Dev Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm db:migrate   # Run pending migrations
pnpm db:seed      # Seed dev data
pnpm test         # Run vitest
pnpm typecheck    # tsc --noEmit
pnpm lint         # eslint + prettier check
```

## Folder Structure

```
src/
  app/                    # Next.js App Router pages and layouts
    (auth)/               # Auth route group (login, register)
    (dashboard)/          # Protected route group
    api/                  # API routes (Route Handlers only)
      [resource]/
        route.ts          # GET, POST, PUT, DELETE in one file per resource
    layout.tsx            # Root layout (providers, fonts, metadata)
    page.tsx              # Landing page
  components/
    ui/                   # Primitives: Button, Input, Card, Dialog
    [feature]/            # Feature-specific components (e.g., billing/, settings/)
  lib/
    db.ts                 # Database singleton + typed query helpers
    auth.ts               # Auth utilities (session, middleware)
    errors.ts             # Custom error classes (AppError, NotFoundError, etc.)
    validation.ts         # Zod schemas shared between client and server
  migrations/             # Sequential SQL migration files
    001_create_users.sql
    002_create_teams.sql
  hooks/                  # Custom React hooks (client-side only)
  types/                  # Shared TypeScript types and interfaces
```

## Rules

### TypeScript

- **strict mode always on.** No `// @ts-ignore`, no `any`. If you can't type it, redesign it.
- Use `interface` for object shapes, `type` for unions and intersections.
- Export types from the module that owns them. Never create a `types.ts` that imports from everywhere.
- Function return types are explicit on exported functions. Inferred on internal ones.

### Database

- **One `db.ts` file** exports the singleton connection and typed helpers:

```typescript
// src/lib/db.ts
import Database from "better-sqlite3";
import path from "node:path";

const DB_PATH = process.env.DB_PATH || path.join(process.cwd(), "data", "app.db");

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
db.pragma("busy_timeout = 5000");

export default db;

export function query<T>(sql: string, ...params: unknown[]): T[] {
  return db.prepare(sql).all(...params) as T[];
}

export function queryOne<T>(sql: string, ...params: unknown[]): T | undefined {
  return db.prepare(sql).get(...params) as T | undefined;
}

export function execute(sql: string, ...params: unknown[]): Database.RunResult {
  return db.prepare(sql).run(...params);
}

export function transaction<T>(fn: () => T): T {
  return db.transaction(fn)();
}
```

- **Never use an ORM.** SQLite is simple enough that raw SQL is clearer and faster. Typed helpers above give us safety without abstraction cost.
- **Migrations are numbered SQL files.** `001_create_users.sql`, `002_create_teams.sql`. Run sequentially. No down migrations — we don't need them for SQLite (just recreate from scratch in dev).
- **Migration runner** is a simple script that reads `migrations/` and tracks applied migrations in a `_migrations` table:

```sql
CREATE TABLE IF NOT EXISTS _migrations (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- **WAL mode always.** Enables concurrent reads while writing. Set in `db.ts` on connection.
- **Foreign keys always ON.** SQLite disables them by default. `PRAGMA foreign_keys = ON` on every connection.
- **Use transactions for multi-statement writes.** SQLite is single-writer; transactions batch writes into one lock acquisition.
- **IDs are `TEXT` ULIDs**, not auto-increment integers. ULIDs are sortable, unique, and safe for distributed systems if we ever migrate. Generate with the `ulid` package.
- **Timestamps are ISO 8601 strings** stored as `TEXT`. SQLite has no native datetime type. Always use `datetime('now')` in SQL or `new Date().toISOString()` in TypeScript.
- **Soft delete with `deleted_at TEXT` column.** Never hard-delete user data. Filter with `WHERE deleted_at IS NULL`.
- **Never use `SELECT *`.** Always list columns explicitly. Schema changes shouldn't silently break queries.

### API Routes (Route Handlers)

- One file per resource: `src/app/api/users/route.ts` handles GET and POST for users.
- Dynamic routes for single resources: `src/app/api/users/[id]/route.ts` handles GET, PUT, DELETE.
- **Always validate input with Zod.** Parse `request.json()` with a schema before touching the database.
- **Return consistent JSON shape:**

```typescript
// Success
return Response.json({ data: user });

// Error
return Response.json({ error: "User not found" }, { status: 404 });

// List
return Response.json({ data: users, total: count });
```

- **Auth check at the top of every protected route.** Use a `getSession(request)` helper that throws if unauthorized.
- **Never expose internal IDs or sensitive fields.** Map database rows to response DTOs explicitly.

### Components

- **Server Components by default.** Only add `"use client"` when you need interactivity (event handlers, hooks, browser APIs).
- **UI primitives in `components/ui/`.** These are generic, reusable, and have no business logic.
- **Feature components in `components/[feature]/`.** These combine UI primitives with business logic.
- **No prop drilling beyond 2 levels.** If you need to pass data deeper, use a Server Component that fetches at the level where it's needed, or a React Context for client state.
- **Forms use Server Actions** for mutations. No `fetch` in client components for writes.
- **Loading states use `loading.tsx`** convention and Suspense boundaries. No manual loading state management.

### Error Handling

- **Custom error classes** in `src/lib/errors.ts`:

```typescript
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code: string = "INTERNAL_ERROR",
  ) {
    super(message);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, "NOT_FOUND");
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super(message, 400, "VALIDATION_ERROR");
  }
}
```

- **API routes catch errors and return structured JSON.** Never let raw Error messages leak to the client.
- **Use `error.tsx` boundary** for page-level errors. Show a user-friendly message, not a stack trace.

### Auth

- **Session stored as signed JWT in HTTP-only cookie.** No localStorage tokens.
- **Middleware in `middleware.ts`** checks auth for protected route groups.
- **Password hashing with `bcrypt` or `@node-rs/argon2`.** Never store plaintext passwords.
- **Rate limit login attempts.** Track in SQLite: `failed_login_attempts` table with IP + timestamp.

### Testing

- **Vitest for unit and integration tests.** No Jest — Vitest is faster and ESM-native.
- **Test database is in-memory:** `new Database(":memory:")` for test isolation.
- **Test file lives next to source:** `db.ts` → `db.test.ts`. No separate `__tests__` directory.
- **Test the behavior, not the implementation.** Assert what the API returns, not which SQL query ran.

## What We Don't Do (and Why)

| Anti-pattern | Why we avoid it |
|---|---|
| `SELECT *` | Schema changes silently break things. List columns explicitly. |
| ORMs (Prisma, Drizzle) | Unnecessary abstraction for SQLite. Raw SQL is faster and clearer. |
| Auto-increment integer IDs | Not portable, not sortable, leak record count. Use ULIDs. |
| `localStorage` for auth | XSS-vulnerable. Use HTTP-only cookies. |
| CSS-in-JS | Runtime cost, bundle bloat. Tailwind is compile-time. |
| Barrel exports (`index.ts`) | Breaks tree-shaking, slows builds. Import from the source file. |
| `"use client"` on everything | Defeats the purpose of RSC. Server Components are the default. |
| `any` type | Unsafe. If you can't type it, the design is wrong. |
| Serverless deployment | SQLite needs a persistent filesystem. Use a VPS. |
| Down migrations | Unnecessary complexity. Recreate from scratch in dev, migrate forward in prod. |
| Global state libraries | React Context + Server Components cover 95% of cases. |
| `.env` in git | Security risk. Use `.env.example` with placeholder values. |
| Comments explaining "what" | The code should be clear. Comments explain "why" only. |

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Files | kebab-case | `user-settings.tsx` |
| Components | PascalCase | `UserSettings` |
| Functions | camelCase | `getUserById` |
| DB tables | snake_case, plural | `team_members` |
| DB columns | snake_case | `created_at` |
| API routes | kebab-case, plural | `/api/team-members` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |
| Types/Interfaces | PascalCase | `TeamMember` |
| Zod schemas | camelCase + Schema suffix | `createUserSchema` |

## Git

- **Conventional commits:** `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- **Branch from `main`.** No develop branch. Ship to main via PR.
- **One concern per commit.** Don't mix refactoring with features.
- **Never commit `data/*.db`.** SQLite databases are in `.gitignore`.
