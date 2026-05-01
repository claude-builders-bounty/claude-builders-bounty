# CLAUDE.md — Next.js 15 + SQLite SaaS

> Production-ready context guide for Claude Code working on a Next.js 15 App Router + SQLite SaaS project.

## Stack & Versions

```
Next.js: 15.x (App Router)
SQLite: better-sqlite3 or @local-first/sync (Turso compatible)
Runtime: Node.js 20+
Package Manager: npm (no pnpm/yarn)
Styling: Tailwind CSS
Auth: NextAuth.js v5 with credentials or OAuth
Deployment: Vercel or Railway
```

## Project Structure

```
/
├── app/                      # Next.js App Router pages
│   ├── (auth)/             # Auth routes (login, register, forgot)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── api/                # API Route Handlers
│   │   ├── auth/           # NextAuth endpoints
│   │   └── [resource]/     # RESTful resource handlers
│   └── layout.tsx
├── components/
│   ├── ui/                 # Shadcn/ui primitives only
│   ├── forms/              # React Hook Form + Zod schemas
│   └── features/            # Feature-specific components
├── lib/
│   ├── db/                 # Database client + migrations
│   │   ├── client.ts       # better-sqlite3 instance
│   │   └── migrations/     # SQL migration files
│   ├── auth/               # Auth utilities
│   └── utils.ts            # Shared helpers
├── scripts/                 # DB seed / migrate scripts
└── CLAUDE.md               # ← You are here
```

**Key rule**: Never put business logic in `app/api/*.ts` directly. Always go through `lib/` modules.

## Naming Conventions

| Thing | Convention | Example |
|-------|------------|---------|
| Pages | `kebab-case` | `app/users/page.tsx` |
| Components | `PascalCase` | `UserCard.tsx` |
| Server actions | `camelCase` | `createUser()` |
| Database tables | `snake_case` | `user_accounts` |
| API routes | `kebab-case` | `app/api/user-profile/route.ts` |
| CSS classes | Tailwind only | `className="text-lg font-medium"` |

## SQL / Migration Conventions

### Migrations

1. All schema changes via migration files in `lib/db/migrations/`
2. Naming: `0001_add_users.sql`, `0002_add_sessions.sql`, etc.
3. **Never run `DROP` or `ALTER` in production migrations** — only additive changes
4. Use `better-sqlite3`'s synchronous API for server components; async for API routes

### Query Patterns

```typescript
// ✅ DO: Use parameterized queries, never string interpolation
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId)

// ❌ DON'T: String interpolation allows SQL injection
const user = db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get()
```

### Transactions

```typescript
// Wrap multi-step operations in transactions
const result = db.transaction(() => {
  const user = db.prepare('INSERT INTO users ...').run(...);
  db.prepare('INSERT INTO sessions ...').run(...);
  return user;
})();
```

## Component Patterns

### Server vs Client Components

- `app/` files with `use client` = interactive UI only
- Everything else = Server Component by default
- **Never** fetch data in client components — use Server Components + `fetch()` with `cache`

### Form Handling

```typescript
// ✅ DO: React Hook Form + Zod everywhere
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});
const form = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

// ❌ DON'T: useState for form state
// ❌ DON'T: uncontrolled inputs for anything beyond trivial forms
```

### Feature Components

Each feature gets its own folder under `components/features/`:

```
components/features/users/
├── UserList.tsx         # Server Component (fetches data)
├── UserListClient.tsx   # Client wrapper for interactivity
├── UserCard.tsx
├── index.ts            # Re-exports
└── UserForm.tsx        # If needed
```

## What We Don't Do (and Why)

| Pattern | Why We Avoid It |
|---------|----------------|
| Class components | React Server Components + functional only |
| `useEffect` for data fetching | Server Components + actions instead |
| Inline styles | Tailwind only, consistent design system |
| `npm run dev` in production | Use proper deployment (Vercel/Railway) |
| Storing secrets in code | Environment variables via `.env.local` |
| `console.log` in production | Use structured logging to stdout |
| Direct `db.exec()` in API routes | Use typed `db.prepare()` with parameterization |

## Dev Commands

```bash
npm run dev          # Start development server (http://localhost:3000)
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed development database
npm run build        # Production build
npm run lint         # ESLint check
npm run type-check   # tsc --noEmit
```

## API Response Pattern

All API routes return this shape:

```typescript
// app/api/example/route.ts
export async function GET(request: Request) {
  try {
    const data = await getExampleData();
    return Response.json({ ok: true, data });
  } catch (error) {
    return Response.json(
      { ok: false, error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 400 }
    );
  }
}
```

## Anti-Patterns to Flag

If Claude Code tries any of these, redirect immediately:

- ❌ `"use server"` in component files (put it in `lib/actions/`)
- ❌ `JSON.parse()` on untrusted input
- ❌ Storing plain-text passwords (must be hashed with bcrypt/argon2)
- ❌ Returning raw database rows as API responses (always validate + transform)
- ❌ `any` type annotations (use `unknown` + type guards instead)
