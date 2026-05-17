# Next.js 15 + SQLite SaaS — Project Context

## 🏗 Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Next.js | 15.x (App Router) | Stable RSC, Server Actions GA |
| React | 19.x | Peer dep for Next.js 15 |
| SQLite | better-sqlite3 11.x | Zero-infra DB, good for single-region SaaS |
| Turso | Optional | Edge-ready SQLite (libsql) |
| Drizzle ORM | 0.38+ | Type-safe, SQL-like, no magic |
| Auth.js | 5.x (NextAuth v5) | Official Next.js auth |
| Tailwind CSS | 4.x | Utility-first, next:build handles purge |
| TypeScript | 5.x | Strict mode always |

## 📁 Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth group (login, register)
│   ├── (dashboard)/       # Authenticated routes
│   │   ├── settings/
│   │   └── [org]/
│   └── api/               # Route handlers (webhooks, external)
├── components/
│   ├── ui/                # Primitive UI (button, input, card)
│   └── features/          # Feature-specific (team-switcher, billing)
├── db/
│   ├── schema/            # Drizzle schema definitions
│   │   └── *.sql.ts
│   ├── migrations/        # Auto-generated (do NOT edit manually)
│   └── index.ts           # DB connection singleton
├── lib/
│   ├── auth.ts            # Auth.js config
│   ├── email.ts           # Resend / SendGrid wrapper
│   └── utils.ts           # Shared helpers (cn(), formatDate())
├── actions/               # Server Actions (one file per domain)
│   ├── team.actions.ts
│   └── billing.actions.ts
└── types/                 # Shared types not in schema
```

### Rules
- **Max 400 lines per file.** If a file exceeds this, split into `domain/` subdir.
- **Server Actions live in `actions/`**, not inline in page components.
- **DB schema files end in `.sql.ts`** to signal they generate SQL.
- **UI components are server-first.** Only add `'use client'` when you need hooks or browser APIs.

## 🗄 SQL / Migration Conventions

### Schema Patterns
```ts
// ✅ Good: explicit table name, timestamps, soft-delete
import { sqliteTable, text, integer, index } from "drizzle-orm/sqlite-core";

export const users = sqliteTable(
  "users",
  {
    id: text("id").primaryKey(),
    email: text("email").notNull().unique(),
    name: text("name"),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .$defaultFn(() => new Date()),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .$defaultFn(() => new Date()),
    deletedAt: integer("deleted_at", { mode: "timestamp" }), // soft-delete
  },
  (t) => ({
    emailIdx: index("idx_users_email").on(t.email),
  })
);
```

### Migration Rules
1. **NEVER edit migration files** after they're generated — Drizzle expects immutability
2. **One migration per deploy** — squash before release: `drizzle-kit push`
3. **Production:** `drizzle-kit migrate` (never `push`)
4. **Foreign keys:** SQLite enforces FK only with `PRAGMA foreign_keys = ON`. Add this in `db/index.ts`

## 🧩 Component Patterns

### Server Component (default)
```tsx
// ✅ Good: data fetching in server component, minimal client islands
export default async function TeamPage() {
  const teams = await db.select().from(teams);
  return <TeamList teams={teams} />;
}
```

### Client Component (opt-in)
```tsx
'use client';
// ✅ Good: only add 'use client' when necessary
export function TeamSwitcher({ teams }: { teams: Team[] }) {
  const [open, setOpen] = useState(false);
  // ...
}
```

## ⚙️ Dev Commands

```bash
# Development
npm run dev                 # Next.js dev server
npm run db:push             # Push schema changes (dev only)
npm run db:generate         # Generate migration files
npm run db:studio           # Drizzle Studio (GUI browser for SQLite)

# Production
npm run build               # Build with TypeScript check
npm run db:migrate          # Run pending migrations
npm start                   # Production server

# Testing
npm run test                # Vitest
npm run test:e2e            # Playwright

# Quality
npm run lint                # ESLint + Prettier
npm run typecheck           # tsc --noEmit (separate from build)
```

## ✅ Patterns to Follow

1. **Route Groups for auth** — Wrap dashboard routes in `(dashboard)/layout.tsx` for auth checks
2. **SearchParams for lists** — Use URL params for pagination/filtering, not useState
3. **Error handling in Actions** — Every Server Action returns `{ success, error, data }` shape
4. **Row Level Security at app layer** — SQLite has no RLS; check org membership in every query
5. **Singleton DB instance** — `db/index.ts` exports a single instance. No `new Database()` elsewhere
6. **Soft-delete all user data** — Never actually DELETE rows that affect billing or audit
7. **Env vars in `zod` schema** — Validate `process.env.X` through a Zod schema at startup

## ❌ Anti-patterns to Avoid

1. **`useEffect` for data fetching** — Use Server Components or Server Actions
2. **Inline `'use client'` in layout files** — Default to server; extract interactive widgets
3. **Manual SQLite migrations** — Always use Drizzle. Never write raw `ALTER TABLE`
4. **Relative imports crossing packages** — Use `@/` path alias consistently
5. **Storing files in SQLite** — Use S3/R2. SQLite BLOBs kill performance
6. **Missing `try/catch` in Actions** — Unhandled Action errors give 500 with no context
7. **Using `any`** — Exception: `unknown` first, cast as last resort

## 🔒 Security Checklist

- [ ] Auth.js configured with adapter(drizzle)
- [ ] API routes validate session: `auth()` at top
- [ ] SQLite file outside `public/` (default in `data/`)
- [ ] Rate limiting on auth routes (use `lru-cache` + headers)
- [ ] CORS only on public API routes
- [ ] Content Security Policy in `next.config.ts`

## 🚀 Quick Start

```bash
npx create-next-app@latest my-saas --typescript --tailwind --eslint
cd my-saas
npm install better-sqlite3 drizzle-orm @auth/core @auth/drizzle-adapter
npm install -D drizzle-kit @types/better-sqlite3
# Paste this CLAUDE.md into root, then:
cp .claude/CLAUDE.md ./CLAUDE.md 2>/dev/null || true
mkdir -p src/db/schema src/lib src/actions
# Open in Claude Code and say: "set up the database for a SaaS app"
```
