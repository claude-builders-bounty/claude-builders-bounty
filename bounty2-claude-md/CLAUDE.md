# Next.js 15 + SQLite SaaS — CLAUDE.md

> **Opinionated, production-ready context file for Claude Code.**
> Stack: Next.js 15 (App Router) · SQLite (better-sqlite3 or Turso) · TypeScript

---

## Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Next.js | 15.x (App Router) | Server Components, caching, streaming |
| React | 19.x | Compatible with Next.js 15 |
| TypeScript | 5.x | Strict mode enabled |
| SQLite | better-sqlite3 **or** Turso (libsql) | Synchronous API preferred; Turso for edge/distributed |
| Drizzle ORM | latest | Type-safe, zero-abstraction SQL migration |
| Tailwind CSS | 4.x | Utility-first, no CSS files to manage |
| next-auth / auth.js | 5.x | Session-based auth (JWT for SQLite) |
| valibot | latest | Zod alternative, smaller bundle, faster |
| react-hook-form | 7.x | Form state, no controlled input overhead |

**Not in stack:**
- ❌ Prisma (too heavy, slow startup on serverless)
- ❌ tRPC (unnecessary indirection; use Server Actions)
- ❌ Redux/Jotai (React Server Components make client state less critical)
- ❌ CSS Modules / styled-components (Tailwind handles everything)

---

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Route group: auth pages
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Route group: authenticated
│   │   ├── layout.tsx      # Sidebar, header, session check
│   │   ├── page.tsx        # Dashboard home
│   │   ├── settings/
│   │   └── api/users/      # Route handlers (API layer)
│   ├── layout.tsx          # Root layout (fonts, providers)
│   ├── globals.css         # Tailwind imports only
│   └── error.tsx           # Error boundary
├── components/
│   ├── ui/                 # Base UI primitives (no logic)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── card.tsx
│   ├── features/           # Feature-specific composed components
│   │   └── billing/
│   └── providers.tsx       # Session, theme, query providers
├── lib/
│   ├── db.ts               # SQLite client singleton
│   ├── auth.ts             # Auth config
│   ├── utils.ts            # formatters, cn() helper
│   └── validations/        # Valibot schemas
├── hooks/                  # Client-side hooks
│   ├── use-debounce.ts
│   └── use-media-query.ts
├── middleware.ts            # Auth redirect, i18n if needed
└── styles/                 # (empty — Tailwind via CSS @import)

drizzle/                     # Drizzle ORM
├── schema.ts                # All table definitions
└── migrations/              # Versioned SQL migration files
```

### Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Folders | kebab-case | `user-settings/` |
| Files | kebab-case | `billing-page.tsx` |
| Components | PascalCase (export) | `ExportButton.tsx` |
| Server actions | camelCase + `action` suffix | `updateUserAction` |
| DB tables | snake_case | `user_sessions` |
| DB columns | snake_case | `created_at` |
| Env vars | UPPER_SNAKE_CASE | `DATABASE_URL` |
| Constants | UPPER_SNAKE_CASE | `MAX_FREE_PROJECTS` |
| Types/interfaces | PascalCase | `UserWithSubscription` |

---

## Database Rules

### Migration Discipline

1. **Every schema change = a migration file.** No manual DB edits in production.
2. **Migrations are ordered:** `0001_initial.sql`, `0002_add_indexes.sql`, etc.
3. **Never drop columns in migration.** Mark as deprecated, remove in next major version.
4. **Always add `created_at` and `updated_at`** timestamp columns.

```sql
-- ✅ Correct migration pattern
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

### Query Patterns

```typescript
// ✅ Do: Use prepared statements (Drizzle handles this)
const user = db.select().from(users).where(eq(users.id, userId)).get();

// ❌ Don't: Raw string interpolation (SQL injection risk)
const user = db.prepare(`SELECT * FROM users WHERE id = '${userId}'`).get();

// ✅ Do: Batch reads when possible
const [user, projects] = await Promise.all([
  getUser(userId),
  getProjectsByUser(userId),
]);
```

### Connection Management

```typescript
// src/lib/db.ts — Singleton pattern (critical for SQLite)
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from '@/drizzle/schema';

const sqlite = new Database(process.env.DATABASE_URL!);
sqlite.pragma('journal_mode = WAL');      // Enable concurrent reads
sqlite.pragma('foreign_keys = ON');        // Enforce referential integrity

export const db = drizzle(sqlite, { schema });
```

**Why WAL mode?** SQLite allows concurrent reads but locks on writes. WAL removes most write contention for SaaS read-heavy workloads.

---

## Component Patterns

### Server vs Client Components

```
Default: Server Component (no 'use client' directive)
Add 'use client' ONLY when you need:
  - onClick, onChange, useState, useEffect
  - Browser APIs (localStorage, window)
  - Libraries that require DOM (chart libraries, dnd)
```

```tsx
// ✅ Server Component (default) — fetch data, render HTML
export default function DashboardPage() {
  const projects = await getProjectsForUser(session.userId);
  return <ProjectList projects={projects} />;
}

// ❌ Don't: Make entire page 'use client' just for one interactive bit
// Instead, extract the interactive part:
'use client';
export function CreateProjectButton() {
  const [open, setOpen] = useState(false);
  return <Dialog open={open} onOpenChange={setOpen}>...</Dialog>;
}
```

### Server Actions for Mutations

```typescript
// ✅ Do: Server Actions for forms
export async function updateProfileAction(formData: FormData) {
  const session = await getSession();
  if (!session) return { error: 'Unauthorized' };

  const data = profileSchema.safeParse(Object.fromEntries(formData));
  if (!data.success) return { errors: data.error.flatten() };

  await db.update(users).set(data.data).where(eq(users.id, session.userId));
  revalidatePath('/settings');
  return { success: true };
}

// ❌ Don't: Create API route handlers for simple mutations
// app/api/users/route.ts ← unnecessary layer for single-operation mutations
```

### Data Fetching Pattern

```tsx
// In Server Component or Server Action — direct DB call
async function Page({ params }: { params: { id: string } }) {
  const project = await getProject(params.id); // Direct DB call, no REST hop
  if (!project) notFound();
  return <ProjectDetail project={project} />;
}

// For client components that need data — pass as props or use SWR/SWR alternative
// Don't fetch inside useEffect. Pass from parent Server Component.
```

---

## Dev Commands

```bash
# Development
npm run dev                  # Start dev server (port 3000)

# Database
npx drizzle-kit generate     # Generate migration from schema changes
npx drizzle-kit migrate      # Run pending migrations
npx drizzle-kit studio       # Visual DB browser (dev only)

# Code quality
npx tsc --noEmit             # Type check (CI gate)
npm run lint                 # ESLint + Prettier
npm run test                 # Vitest

# Build & run
npm run build                # Production build
npm start                    # Start production server
```

---

## Anti-Patterns (Don't Do These)

### 1. Fetching in `useEffect`
```tsx
// ❌ Waterfall of loading states, no SEO, no streaming
useEffect(() => {
  fetch('/api/projects').then(r => r.json()).then(setProjects);
}, []);

// ✅ Fetch in Server Component, pass props down
const projects = await getProjects(); // Top-level await in RSC
```

### 2. Wrapping everything in Suspense boundary
```tsx
// ❌ Lazy loading indicator everywhere
<Suspense fallback={<Skeleton />}>
  <ExpensiveComponent />
</Suspense>

// ✅ Only wrap slow/data-dependent parts
// Let fast UI render immediately
```

### 3. Giant `page.tsx` files (>200 lines)
```tsx
// ❌ One file does everything
export default function DashboardPage() {
  // 500 lines of mixed logic, queries, and JSX
}

// ✅ Extract server actions, queries, sub-components
// Keep page.tsx as an orchestrator (< 80 lines)
```

### 4. Ignoring SQLite limits
- **No `JOIN` on millions of rows** — SQLite is embedded, not a distributed query engine
- **Use indexes on every `WHERE`/`JOIN`/`ORDER BY` column**
- **`PRAGMA foreign_keys = ON` is mandatory** — SQLite defaults to OFF
- **Connection limit: 1 writer at a time** — use WAL mode for read concurrency

### 5. Storing secrets in code/env without validation
```typescript
// ❌ Silent failure
const db = new Database(process.env.DATABASE_URL);

// ✅ Fail fast at startup
const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) throw new Error('DATABASE_URL is required');
const db = new Database(dbUrl);
```

---

## Environment Variables Required

```env
# .env.local (gitignored)
DATABASE_URL=./data/app.sqlite          # better-sqlite3 file path
# OR for Turso:
# DATABASE_URL=libsql://your-db.turso.io
# TURSO_AUTH_TOKEN=xxx

AUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000

# Optional
NODE_ENV=development
```

---

## Testing Strategy

| Layer | Tool | What to test |
|-------|------|-------------|
| Unit | Vitest | Utils, validations, pure functions |
| Integration | Vitest + msw | Server Actions, DB queries (in-memory SQLite) |
| E2E | Playwright | Critical user flows (login → create → delete) |

```bash
# Run unit tests
npm run test

# Run E2E (requires dev server)
npm run test:e2e
```

---

## Performance Rules

1. **`revalidatePath` after mutations** — don't rely on `cache: no-store` everywhere
2. **Dynamic imports for heavy client libs** — charts, editors, rich text
3. **Generate static params for semi-static content** — `generateStaticParams()` for docs, blog
4. **Image optimization** — always use `<Image />` from `next/image`, never `<img>`
5. **Bundle analysis** — `next build --analyze` before every deploy to catch bloat

---

*This CLAUDE.md is designed for greenfield Next.js 15 + SQLite SaaS projects. Every rule exists because we learned it the hard way.*
