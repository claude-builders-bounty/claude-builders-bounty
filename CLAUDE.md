# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Node.js**: 20+ (LTS)
- **Next.js**: 15.x (App Router)
- **SQLite**: better-sqlite3 (sync) or @libsql/client (Turso)
- **React**: 19.x
- **TypeScript**: 5.x strict mode

## Project Structure

```
app/                    # Next.js App Router pages
  (auth)/              # Auth-related routes (login, register)
  (dashboard)/         # Protected dashboard routes
  api/                  # API routes
    webhooks/           # External webhook handlers
components/
  ui/                   # Base UI components (Button, Input, etc.)
  forms/                # Form components with react-hook-form
  features/             # Feature-specific components
lib/
  db/                   # Database client & schema
    migrations/          # SQL migration files
    schema.ts           # Drizzle schema definitions
  auth/                 # Auth utilities (session, token)
  api/                   # API client utilities
hooks/                  # Custom React hooks
types/                  # Shared TypeScript types
```

## SQL / Migration Conventions

### Migration Rules
- **One table per migration** — keep migrations focused
- **Use Drizzle ORM** — never raw SQL for schema changes
- **Never alter existing columns** — only add nullable columns or new tables
- **Always add `created_at` and `updated_at`** — use `INTEGER DEFAULT (unixepoch())` for SQLite
- **Indexes on foreign keys** — always index `user_id`, `tenant_id` columns

### Schema Patterns
```typescript
// ✅ CORRECT — define table schema
export const users = sqliteTable('users', {
  id: text('id').primaryKey(), // UUID
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
});

// ❌ WRONG — don't use serial id on SQLite
export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }), // Avoid
});
```

### Query Patterns
```typescript
// ✅ CORRECT — prepared statements for repeated queries
const getUserById = db.query.users.findFirst({
  where: eq(users.id, sql.placeholder('id')),
}).prepare('get_user_by_id');

// ❌ WRONG — raw string interpolation
const user = db.execute(`SELECT * FROM users WHERE id = '${id}'`);
```

## Component Patterns

### File Naming
- **PascalCase** for components: `UserProfile.tsx`
- **camelCase** for utilities: `formatCurrency.ts`
- **kebab-case** for pages/routes: `app/(dashboard)/billing/page.tsx`

### Component Structure
```typescript
// ✅ CORRECT — explicit props + co-located tests
interface UserCardProps {
  user: { id: string; email: string; name: string | null };
  onSelect?: (id: string) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect?.(user.id)}>
      {user.name ?? user.email}
    </div>
  );
}

// ❌ WRONG — prop drilling, implicit dependencies
export function UserCard(props: any) {
  const user = useUser(); // Hidden dependency
  // ...
}
```

### Server vs Client Components
- **Server Components by default** — use `'use client'` only when needed
- **Keep client boundaries small** — isolate `'use client'` to form components
- **Pass serializable data** — never pass functions/callbacks to Server Components

## Patterns We Follow

### Error Handling
```typescript
// ✅ CORRECT — predictable errors with result pattern
type Result<T, E = Error> = { ok: true; data: T } | { ok: false; error: E };

async function getUser(id: string): Promise<Result<User>> {
  const user = await db.query.users.findFirst({ where: eq(users.id, id) });
  if (!user) return { ok: false, error: new Error('User not found') };
  return { ok: true, data: user };
}

// ❌ WRONG — throwing in expected paths
async function getUser(id: string) {
  const user = await db.query.users.findFirst({ where: eq(users.id, id) });
  if (!user) throw new Error('User not found'); // Expected = not error
  return user;
}
```

### Environment Variables
```bash
# ✅ REQUIRED — always prefix with NEXT_PUBLIC_ for client-exposed vars
NEXT_PUBLIC_APP_URL=http://localhost:3000

# ✅ PRIVATE — server-only vars (no prefix)
DATABASE_URL=file:./data/app.db
OPENAI_API_KEY=sk-...
```

## What We DON'T Do (And Why)

### ❌ No Server Actions for mutations that need validation
- Use API routes with explicit request/response for anything beyond simple CRUD
- Server Actions bypass API layer middleware (rate limiting, auth checks)

### ❌ No `any` types
- Use `unknown` and narrow with type guards if schema is unknown
- Exception: third-party API responses with explicit ignore comment

### ❌ No class components
- Use function components + hooks only
- Exception: legacy migration refactoring (marked with `// legacy:` comment)

### ❌ No direct `localStorage` / `sessionStorage` for auth tokens
- Use `httpOnly` cookies only — XSS can access localStorage
- Exception: non-sensitive UI state (theme, preferences)

### ❌ No database migrations that delete columns
- SQLite doesn't support `DROP COLUMN` efficiently until 3.35.0
- Mark columns deprecated instead, remove in major version

## Dev Commands

```bash
# Install dependencies
npm install

# Run database migrations
npm run db:migrate

# Start development server
npm run dev

# Run type checking
npm run typecheck

# Run linting
npm run lint

# Run tests
npm run test
```

## API Design

### Request/Response Pattern
```typescript
// ✅ CORRECT — consistent API envelope
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

// POST /api/users
// Request: { email: string; name?: string }
// Response: ApiResponse<{ id: string; email: string }>
```

### Status Codes
- `200` — Success with data
- `201` — Resource created
- `400` — Validation error (include field-level errors)
- `401` — Not authenticated
- `403` — Authenticated but not authorized
- `404` — Resource not found
- `429` — Rate limited
- `500` — Server error (never expose stack traces)

## Testing Conventions

```typescript
// ✅ Unit test patterns
describe('getUserById', () => {
  it('returns user when found', async () => {
    const result = await getUserById('user_123');
    expect(result.ok).toBe(true);
    expect(result.data?.email).toBe('test@example.com');
  });

  it('returns error when not found', async () => {
    const result = await getUserById('nonexistent');
    expect(result.ok).toBe(false);
  });
});

// ❌ WRONG — tests that depend on external state
it('works correctly', async () => {
  const user = await fetchUserFromAPI(); // Flaky
});
```
