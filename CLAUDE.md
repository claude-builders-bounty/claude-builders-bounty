# CLAUDE.md - Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Runtime**: Node.js 20+ (LTS)
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via `better-sqlite3` or `@libsql/client` (Turso)
- **Language**: TypeScript 5.x (strict mode)
- **Styling**: Tailwind CSS 3.x
- **Auth**: NextAuth.js v5 or Clerk
- **Deployment**: Vercel / Railway / Fly.io

## Project Structure

```
/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth group route (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Protected dashboard routes
│   │   ├── layout.tsx     # Auth guard + sidebar
│   │   ├── page.tsx       # Dashboard home
│   │   └── settings/page.tsx
│   ├── api/               # API routes
│   │   ├── auth/[...nextauth]/route.ts
│   │   └── webhooks/
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/               # Shadcn/ui base components
│   ├── forms/            # React Hook Form + Zod schemas
│   └── features/         # Feature-specific components
├── lib/
│   ├── db.ts             # SQLite client singleton
│   ├── migrations/       # Database migrations
│   │   └── migrate.ts    # Migration runner
│   ├── auth.ts           # NextAuth config
│   └── utils.ts          # Utility functions
├── db/                    # SQLite database file
│   └── *.db              # SQLite files (gitignored)
├── drizzle/              # Drizzle ORM (if using)
├── public/               # Static assets
├── scripts/
│   └── seed.ts           # Database seeding
├── .env.local            # Environment variables
└── next.config.ts       # Next.js config
```

## SQL / Migration Conventions

### Rules
1. **All schema changes** must go through migrations — never modify `db/schema.ts` and run directly
2. **Migrations are versioned**: `0001_add_users.sql`, `0002_add_subscriptions.sql`
3. **Never write raw SQL** in API routes — use Drizzle ORM or the query builder
4. **Index foreign keys** on read-heavy columns
5. **Soft deletes preferred**: use `deleted_at` column instead of `DELETE`

### Migration Flow
```bash
# Create a new migration
pnpm db:generate "add_users_table"

# Run migrations
pnpm db:migrate

# Check migration status
pnpm db:status
```

### Allowed Raw SQL
Only for:
- Complex aggregations (`GROUP BY`, `HAVING`)
- Full-text search
- Performance-critical queries (with comment explaining why)

## Component Patterns

### Server Components (Default)
Use `"use client"` only when necessary:
- User interactions (click, hover)
- useState / useEffect / useRef
- Browser APIs

```tsx
// ✅ Good - Server Component
export default async function DashboardPage() {
  const data = await db.query.users.findMany()
  return <div>{data.length} users</div>
}

// ✅ Good - Client Component boundary
"use client"
export function UserList({ users }: { users: User[] }) {
  const [filter, setFilter] = useState("")
  return <input onChange={e => setFilter(e.target.value)} />
}
```

### Form Handling
Always use React Hook Form + Zod:
```tsx
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})
// Use in component with useForm
```

### Error Handling
- API routes: throw `NextResponse.json({ error: "message" }, { status: 400 })`
- Components: use `error.tsx` and `loading.tsx` files
- Never swallow errors

## Anti-Patterns to Avoid

| Anti-Pattern | Why | Instead |
|---|---|---|
| `DELETE FROM users` without WHERE | Catastrophic data loss | Always add `WHERE id = ? AND deleted_at IS NULL` |
| `rm -rf node_modules && npm install` | Destroys lockfile consistency | `npm ci` or `pnpm install --frozen-lockfile` |
| `git push --force` to main | Rewrites shared history | `git push --force-with-lease` or merge |
| `SELECT *` | Fetches unnecessary data | List specific columns |
| Sync DB operations in API routes | Blocks response | Use async/await with proper error handling |
| Storing secrets in code | Security breach | Use `.env.local` + env vars |
| Inline styles | Maintenance nightmare | Tailwind utility classes |

## Database Schema Rules

### Users Table
```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY DEFAULT (uuid4()),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT, -- NULL for OAuth-only
  email_verified INTEGER DEFAULT 0,
  created_at INTEGER DEFAULT (unixepoch()),
  updated_at INTEGER,
  deleted_at INTEGER -- Soft delete
);
```

### Indexes
Always add indexes on:
- Foreign key columns
- Columns used in WHERE clauses
- Columns used for authentication (email, etc.)

## What We Don't Do (And Why)

1. **No `npm install` in production** — use `npm ci` to guarantee exact versions
2. **No direct SQLite writes from client** — always through API routes with auth checks
3. **No Promises without error handling** — every async call needs try/catch or `.catch()`
4. **No `console.log` in production code** — use a logger (pino, winston)
5. **No magic numbers** — extract to constants with meaningful names
6. **No mixing auth strategies** — pick one (NextAuth or Clerk, not both)

## Dev Commands

```bash
pnpm dev          # Start dev server (http://localhost:3000)
pnpm build        # Production build
pnpm db:migrate   # Run pending migrations
pnpm db:generate  # Generate types from schema
pnpm db:push      # Push schema (dev only, destructive)
pnpm db:seed      # Seed database with test data
pnpm lint         # ESLint
pnpm type-check   # TypeScript check
```

## Environment Variables

```env
# Required
DATABASE_URL=file:./db/production.db
NEXTAUTH_SECRET=     # openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000

# Optional
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
TURSO_DATABASE_URL=  # For Turso cloud SQLite
```
