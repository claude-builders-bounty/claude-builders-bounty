# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via `better-sqlite3` (local) or `@libsql/client` (Turso remote)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 with Credentials + OAuth
- **Styling**: Tailwind CSS
- **Validation**: Zod (shared between client + server)
- **Deployment**: Vercel (frontend) + Railway/LiLz Wing (SQLite)

---

## Project Structure

```
app/
  (auth)/              # Auth routes (login, register, forgot-password)
  (dashboard)/         # Protected routes — all require session
  api/
    auth/              # NextAuth handlers only
    v1/                # REST API versioned here
      users/
      subscriptions/
components/
  ui/                  # Base: Button, Input, Card, Modal, Badge (Radix primitives)
  features/            # Feature modules: auth/, billing/, settings/
lib/
  db.ts                # DB client singleton — ONLY file that imports better-sqlite3
  schema.ts            # Drizzle schema — all table definitions
  auth.ts              # NextAuth config
  validators/          # Zod schemas shared client ↔ server
middleware.ts          # Auth guard — redirects unauthenticated users
```

**Rule #1**: Only `lib/db.ts` touches SQLite. No DB imports anywhere else.

---

## Database Rules

### Migrations

```bash
# 1. Edit lib/schema.ts
# 2. Generate migration
npx drizzle-kit generate

# 3. Apply to local DB
npx drizzle-kit migrate

# 4. Production: migration runs automatically on deploy ( Railway/LiLz Wing)
```

**Never** modify existing migration files. Never run raw SQL in API routes — always use Drizzle.

### Query Patterns

```typescript
// ✅ Correct — parameterized, with error handling
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// ✅ Better — Drizzle ORM (type-safe)
const user = await db.select().from(users).where(eq(users.id, userId));

// ❌ Dangerous — SQL injection via string interpolation
const user = await db.prepare(\`SELECT * FROM users WHERE id = '\${id}'\`);
```

### Transactions

```typescript
await db.transaction(async (tx) => {
  await tx.insert(orders).values({ userId, total });
  await tx.update(users).set({ credits: user.credits - total }).where(eq(users.id, userId));
});
```

---

## Component Rules

### UI Components (components/ui/)

- Use **Radix UI** primitives as base. Never build accessible components from scratch.
- One component per file. No barrel exports from `components/ui/index.ts`.
- Props are typed with TypeScript interfaces, not inferred.

### Feature Components (components/features/)

- One feature per directory: `components/features/billing/`
- Feature components may only import from `components/ui/` and `lib/`
- No prop-drilling more than 2 levels — use Context or Zustand

### Anti-Patterns

```typescript
// ❌ No 'any' — use Zod to infer types
const data: any = fetchSomething();

// ❌ No inline styles — use Tailwind utility classes

// ❌ No direct DOM manipulation in React components

// ❌ No prop-drilling > 2 levels — use Context
```

---

## API Routes (app/api/)

### Rules

1. **Always validate input** with Zod schema before touching DB
2. **Always return structured JSON**: `{ data, error, meta }`
3. **Never expose raw SQLite errors** to client
4. **Always check session** with `auth()` before mutating data

### Response Format

```typescript
// Success
return Response.json({ data: { user }, error: null, meta: {} });

// Error
return Response.json({ data: null, error: 'User not found', meta: {} }, { status: 404 });

// Validation error
return Response.json({ data: null, error: 'Invalid input', meta: { issues: result.error.issues } }, { status: 400 });
```

---

## What We Don't Do (And Why)

| Practice | Why We Avoid It |
|----------|-----------------|
| Direct `better-sqlite3` imports in API routes | DB connection pooling is managed in `db.ts` — importing elsewhere breaks it |
| `use client` for everything | Server Components are faster and cheaper — only use `'use client'` when you need interactivity |
| Magic numbers in code | Use named constants: `MAX_FILE_SIZE = 10 * 1024 * 1024` |
| `console.log` in API routes | Use structured logging with `warn`/`error` levels only |
| Skipping Zod validation | Unvalidated input is a security risk — validate at API boundary |
| Global CSS where modules work | Tailwind + CSS Modules prevent style bleed |

---

## Development Commands

```bash
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run db:studio    # Open Drizzle Studio (database GUI)
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed local DB with test data
```

## Testing

```bash
npm test             # Unit tests (Vitest)
npm run test:e2e     # E2E tests (Playwright)
```

---

_Modified for Next.js 15 App Router + SQLite SaaS. Update this file when stack decisions change._
