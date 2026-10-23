# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Blueprint

> Production-ready guidance, conventions, and constraints for Claude Code.

---

## 1. High-Level Architecture & Tech Stack

- **Framework**: Next.js 15 (React 19, App Router exclusively; no `pages/` directory).
- **Language**: TypeScript (strict mode, no `any`, explicit interfaces/types).
- **Styling**: Tailwind CSS v4 / shadcn/ui.
- **Database**: SQLite via `better-sqlite3` (local/VPS) or `libsql` / Turso (distributed edge).
- **ORM / Query Builder**: Drizzle ORM (lightweight, zero-runtime-overhead SQL-like syntax).
- **Auth**: Lucia Auth or NextAuth v5 (session tokens in secure HTTP-only cookies).
- **Validation**: Zod (runtime input validation for Server Actions and API Route Handlers).
- **Testing**: Vitest (unit/integration) + Playwright (E2E).

---

## 2. Strict Negative Constraints (DO NOT BREAK)

- **DO NOT** use `use client` unless the component explicitly requires React state (`useState`, `useEffect`) or browser APIs. Default to React Server Components (RSC).
- **DO NOT** import database clients, secrets, or server actions inside Client Components. Use Server Actions or API Route Handlers with explicit Zod validation.
- **DO NOT** run SQLite mutations without WAL mode enabled (`PRAGMA journal_mode = WAL;`) and Foreign Key constraints active (`PRAGMA foreign_keys = ON;`).
- **DO NOT** execute raw unsanitized SQL strings; always use parameterized queries or Drizzle query builders.
- **DO NOT** introduce mock or synthetic data into production database tables.

---

## 3. Project Directory Structure

```text
my-saas/
├── app/                      # App router routes and server layouts
│   ├── (auth)/               # Route group: login, signup, forgot-password
│   ├── (dashboard)/          # Route group: protected dashboard & settings
│   ├── api/                  # Route handlers (webhooks, public APIs)
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Public landing page
├── components/               # Reusable UI components
│   ├── ui/                   # Primitive components (buttons, dialogs, inputs)
│   └── dashboard/            # Feature-specific dashboard widgets
├── db/                       # Database layer
│   ├── schema.ts             # Drizzle table schemas and relationships
│   ├── index.ts              # SQLite database client & connection singleton
│   └── migrations/           # Drizzle migration files
├── lib/                      # Core business logic and server utilities
│   ├── auth.ts               # Authentication session management
│   ├── env.ts                # Validated environment variables (t3-env / zod)
│   └── utils.ts              # Formatting & helper functions
└── tests/                    # Automated testing suite
```

---

## 4. Database Best Practices (SQLite in Production)

### Connection Singleton (`db/index.ts`)
```typescript
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL || "./data/app.db", {
  timeout: 5000,
});

// Mandatory Pragmas for high-throughput concurrency
sqlite.pragma("journal_mode = WAL;");
sqlite.pragma("synchronous = NORMAL;");
sqlite.pragma("foreign_keys = ON;");

export const db = drizzle(sqlite, { schema });
```

---

## 5. Development & Testing Commands

- **Run Dev Server**: `pnpm dev` (runs on `http://localhost:3000`)
- **Run Unit Tests**: `pnpm test` (Vitest)
- **Run Database Migrations**: `pnpm drizzle-kit push` or `pnpm drizzle-kit migrate`
- **Lint & Typecheck**: `pnpm lint && pnpm tsc --noEmit`
