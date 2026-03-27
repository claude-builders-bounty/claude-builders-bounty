# Claude Code Context - Next.js 15 + SQLite SaaS

## Stack & Versions

- **Next.js**: 15+ (App Router only - no Pages Router)
- **React**: 19+
- **TypeScript**: 5.8+
- **Database**: SQLite via `better-sqlite3`
- **Node.js**: 20+ LTS

## Folder Structure

```
src/
├── app/                    # App Router routes
│   ├── (auth)/            # Route groups for layout organization
│   ├── (dashboard)/       # Authenticated routes
│   ├── api/               # Route handlers
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── ui/               # Reusable UI primitives
│   ├── forms/            # Form components
│   └── features/         # Feature-specific components
├── lib/                  # Shared utilities
│   ├── db.ts             # Database singleton & connection
│   ├── queries/          # SQL query functions (organized by table)
│   └── utils.ts          # General utilities
├── migrations/           # Database migrations
├── types/                # TypeScript types/schemas
└── middleware.ts         # Next.js middleware (auth, etc.)
```

**Why**: Route groups `(name)` let you share layouts without affecting URLs. Separating `lib/queries/` keeps SQL logic organized and testable.

---

## Naming Conventions

| Context | Convention | Example |
|---------|------------|---------|
| Files/Folders | `kebab-case` | `user-profile.tsx`, `api/routes/` |
| React Components | `PascalCase` | `UserProfile`, `DataTable` |
| Functions/Variables | `camelCase` | `getUserById`, `formatDate` |
| Database Tables | `snake_case` | `user_profiles`, `api_keys` |
| Database Columns | `snake_case` | `created_at`, `is_active` |
| TypeScript Types | `PascalCase` | `UserProfile`, `DbUser` |
| Environment Variables | `SCREAMING_SNAKE_CASE` | `DATABASE_URL`, `JWT_SECRET` |

**Why**: `kebab-case` files avoid case-insensitive filesystem issues. `snake_case` in databases is standard SQL practice. `PascalCase` components signals React/TypeScript convention.

---

## Component Patterns

### Default: Server Components

```typescript
// ✅ GOOD - Server Component (default)
export default async function UserProfile({ userId }: { userId: string }) {
  const user = await getUserById(userId);
  return <div>{user.name}</div>;
}
```

**Why**: Server Components reduce client JS bundle, enable direct database access, and improve performance.

### Use Client Components Only When Needed

Add `'use client'` ONLY for:
- Browser APIs (`window`, `localStorage`, etc.)
- React hooks (`useState`, `useEffect`, event handlers)
- Interactive UI (modals, dropdowns, forms with real-time validation)

```typescript
// ✅ GOOD - Client Component with clear purpose
'use client';

export function LoginForm() {
  const [email, setEmail] = useState('');
  // ...
}
```

### Composition Pattern: Server → Client Boundary

```typescript
// ✅ GOOD - Server Component fetches data, passes to Client Component
export default async function DashboardPage() {
  const data = await fetchDashboardData();

  return <DashboardClient initialData={data} />;
}
```

**Why**: Keeps data fetching on server, interactivity on client. Minimizes client JS while maintaining interactivity.

---

## SQL & Database Rules

### 1. Use Prepared Statements Only

```typescript
// ✅ GOOD
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(userId);

// ❌ FORBIDDEN - SQL injection risk
const user = db.exec(`SELECT * FROM users WHERE id = ${userId}`);
```

**Why**: Prevents SQL injection. `better-sqlite3` throws on unsafe operations.

### 2. All Schema Changes Via Migrations

```bash
# ✅ GOOD - Named migration
migrations/20250327_120000_create_users.sql
```

```sql
-- migrations/20250327_120000_create_users.sql
-- UP
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

-- DOWN
DROP TABLE users;
```

**Why**: Migrations provide version control, rollback capability, and reproducible deployments.

### 3. Migration Naming Format

Use `YYYYMMDD_HHMMSS_descriptive_name.sql` format.

**Why**: Timestamps sort chronologically. Descriptive names make migrations self-documenting.

### 4. Query Organization

```
lib/queries/
├── users.ts          # All user-related queries
├── sessions.ts       # Auth/session queries
└── analytics.ts      # Analytics queries
```

```typescript
// lib/queries/users.ts
import { db } from '@/lib/db';

export const usersQueries = {
  findById: db.prepare('SELECT * FROM users WHERE id = ?'),
  findByEmail: db.prepare('SELECT * FROM users WHERE email = ?'),
  create: db.prepare('INSERT INTO users (id, email) VALUES (?, ?)'),
};

// Usage
export function getUserById(id: string) {
  return usersQueries.findById.get(id);
}
```

**Why**: Centralized queries are easier to test, optimize, and maintain. Prepared statements cached at startup.

### 5. Database Connection Singleton

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    const dbPath = process.env.DATABASE_PATH ?? path.join(process.cwd(), 'data.db');
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL'); // Enable WAL for better concurrency
  }
  return db;
}
```

**Why**: Singleton prevents multiple connections. WAL mode enables concurrent reads.

---

## Migrations

### Running Migrations

```bash
# Apply all pending migrations
npm run migrate

# Rollback last migration
npm run migrate:rollback

# Create new migration
npm run migrate:create --name create_users_table
```

### Migration Template

```sql
-- migrations/20250327_120000_description.sql

-- === UP ===
-- Add your schema changes here

-- === DOWN ===
-- Revert your schema changes here
```

**Why**: UP/DOWN structure enables rollbacks. Comments make migrations self-explanatory.

---

## TypeScript & Types

### Database Types

```typescript
// types/database.ts
export interface DbUser {
  id: string;
  email: string;
  created_at: string;
}

// Row types from queries
export type UserInsert = Omit<DbUser, 'id' | 'created_at'>;
```

**Why**: Type safety catches errors at compile time. Separating `Db` prefix from API types prevents confusion.

---

## Anti-Patterns (Forbidden)

### ❌ useState in Server Components

```typescript
// FORBIDDEN
export default function UserProfile() {
  const [count, setCount] = useState(0); // ❌ Server Components can't use hooks
  return <div>{count}</div>;
}
```

**Why**: Server Components run on server, React hooks only work in client components.

### ❌ Direct DOM Manipulation

```typescript
// FORBIDDEN
document.getElementById('app').innerHTML = '...'; // ❌ Never do this
```

**Why**: React manages the DOM. Direct manipulation breaks React's virtual DOM and causes bugs.

### ❌ SQL String Concatenation

```typescript
// FORBIDDEN
const query = `SELECT * FROM users WHERE name = '${userName}'`; // ❌ SQL injection
```

**Why**: SQL injection vulnerability. Always use prepared statements with `?` placeholders.

### ❌ Client-Side Secrets

```typescript
// FORBIDDEN - Exposes secret to browser
const apiKey = process.env.SECRET_KEY;
```

**Why**: Client code can be inspected. Secrets must stay on server (API routes, Server Components).

### ❌ Mixed Client/Server in One File

```typescript
// FORBIDDEN - Don't export both Server and Client Components from same file
export default async function ServerComponent() { /* ... */ }
export function ClientComponent() { 'use client'; /* ... */ }
```

**Why**: Confusing boundary. Separate files make Server/Client distinction explicit.

---

## Development Commands

```bash
# Development
npm run dev              # Start dev server (localhost:3000)

# Building
npm run build            # Production build
npm start                # Start production server

# Code Quality
npm run lint             # ESLint
npm run lint:fix         # Auto-fix lint issues
npm run type-check       # TypeScript check (no emit)

# Database
npm run migrate          # Apply pending migrations
npm run migrate:rollback # Rollback last migration
npm run migrate:create   # Generate new migration file

# Testing
npm run test             # Run Vitest tests
npm run test:watch       // Watch mode
npm run test:coverage    # Coverage report
```

---

## Testing

### Test File Location

```
src/
├── lib/
│   └── queries/
│       ├── users.ts
│       └── users.test.ts    # Co-located test file
```

**Why**: Co-located tests are easier to find and maintain.

### Test Naming

- Test files: `*.test.ts`
- Describe real-world behavior, not implementation details

```typescript
// users.test.ts
import { describe, it, expect } from 'vitest';
import { getUserById } from './users';

describe('getUserById', () => {
  it('returns user when exists', async () => {
    const user = await getUserById('123');
    expect(user?.email).toBe('test@example.com');
  });

  it('returns null when not found', async () => {
    const user = await getUserById('nonexistent');
    expect(user).toBeNull();
  });
});
```

**Why**: Behavior-focused tests survive refactoring. Implementation details couple tests to code structure.

### Database Testing

Use in-memory SQLite for tests:

```typescript
// vitest.setup.ts
import Database from 'better-sqlite3';

export function setupTestDb() {
  const db = new Database(':memory:');
  // Run migrations...
  return db;
}
```

**Why**: In-memory DB is fast and isolated. Each test gets a clean slate.

---

## API Routes

```typescript
// src/app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getUsers } from '@/lib/queries/users';

export async function GET(request: NextRequest) {
  const users = await getUsers();
  return NextResponse.json(users);
}
```

**Why**: Route handlers are Server Functions by default. Direct database access, no API layer needed.

---

## Environment Variables

Create `.env.local` (gitignored):

```bash
DATABASE_PATH=./data/dev.db
SESSION_SECRET=your-secret-here
```

**Why**: `.env.local` overrides `.env` for local development. Never commit secrets.

---

## Performance Guidelines

1. **Cache Database Connections**: Use singleton pattern in `lib/db.ts`
2. **Use Static Rendering**: Mark pages with `export const dynamic = 'auto'` (default) or `'force-static'` where possible
3. **Avoid `fetch` in Server Components** when DB access is possible
4. **Lazy Load Client Components**: Use `dynamic` import for heavy client-side libraries

**Why**: Reduces database load, improves TTFB, minimizes client bundle size.

---

## When to Ask for Clarification

Before implementing, ask if:
- Requirements conflict with these rules
- Database schema design is unclear
- Authentication/authorization approach not specified
- Performance requirements not defined

**Why**: These rules cover 95% of cases. Edge cases need explicit decisions.
