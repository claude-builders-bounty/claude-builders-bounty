# CLAUDE.md — Next.js + SQLite SaaS Starter

## Project Overview

A production-ready Next.js 14 (App Router) starter with SQLite (better-sqlite3) for building SaaS applications. Includes authentication, database schema, API routes, and common patterns for multi-tenant SaaS.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Database:** SQLite via better-sqlite3
- **ORM:** Kysely (type-safe SQL builder)
- **Auth:** NextAuth.js with credentials provider
- **Styling:** Tailwind CSS
- **Deployment:** Vercel / Node.js adapter

## Database Schema

### Core Tables

```sql
-- Users (stored in _users table to avoid conflicts)
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Organizations (for multi-tenancy)
CREATE TABLE organizations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'free',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Organization membership
CREATE TABLE members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  role TEXT DEFAULT 'member',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, organization_id)
);

-- Example: Tasks table for a todo app
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending',
  created_by INTEGER NOT NULL REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Important Notes

- Table names prefixed with underscore (`_users`) to avoid SQL reserved word conflicts
- All tables include `organization_id` for multi-tenant isolation
- Use Kysely's type-safe queries instead of raw SQL where possible

## Project Structure

```
/
├── app/                    # Next.js App Router pages
│   ├── api/               # API routes
│   │   ├── auth/           # NextAuth endpoints
│   │   ├── tasks/          # Task CRUD endpoints
│   │   └── organizations/ # Organization management
│   ├── (auth)/            # Auth pages (login, register)
│   ├── dashboard/         # Protected dashboard
│   └── layout.tsx          # Root layout with providers
├── components/             # React components
├── lib/                    # Core utilities
│   ├── db.ts               # Database connection (singleton)
│   ├── auth.ts             # Auth configuration
│   └── kysely.ts           # Kysely instance
├── migrations/             # SQL migrations
└── types/                  # TypeScript types
```

## Key Patterns

### Database Queries (Kysely)

```typescript
import { db } from '@/lib/db';

// Select with joins
const tasks = await db
  .selectFrom('tasks')
  .innerJoin('users', 'tasks.created_by', 'users.id')
  .select(['tasks.*', 'users.email as creator_email'])
  .where('tasks.organization_id', '=', orgId)
  .execute();

// Insert with returning
const [newTask] = await db
  .insertInto('tasks')
  .values({ title, organization_id: orgId, created_by: userId })
  .returningAll()
  .execute();
```

### API Routes

```typescript
// app/api/tasks/route.ts
import { getServerSession } from 'next-auth';
import { db } from '@/lib/db';

export async function GET(req: Request) {
  const session = await getServerSession();
  if (!session?.user) return new Response('Unauthorized', { status: 401 });
  
  const tasks = await db
    .selectFrom('tasks')
    .where('organization_id', '=', session.user.organizationId)
    .execute();
  
  return Response.json(tasks);
}
```

### Middleware for Auth Protection

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const token = req.cookies.get('next-auth.session-token');
  if (!token && !req.nextUrl.pathname.startsWith('/auth')) {
    return NextResponse.redirect(new URL('/auth/login', req.url));
  }
  return NextResponse.next();
}
```

## Environment Variables

```env
# Database
DATABASE_URL=file:./data/app.db

# Auth (generate with: openssl rand -base64 32)
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000

# Optional: Email (for password reset)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=pass
```

## Running Locally

```bash
# Install dependencies
npm install better-sqlite3 @auth/kysely-adapter kysely next-auth

# Create database and run migrations
npm run db:migrate

# Seed demo data
npm run db:seed

# Start dev server
npm run dev
```

## Common Tasks

### Adding a New Table

1. Create migration in `migrations/`
2. Add type definition to `lib/types.ts`
3. Create API route in `app/api/`
4. Add to frontend with React Query or Server Actions

### Adding Authentication to a Page

```typescript
// Server Component
import { getServerSession } from 'next-auth';

export default async function Page() {
  const session = await getServerSession();
  if (!session) redirect('/auth/login');
  
  return <div>Welcome {session.user.email}</div>;
}
```

### Deployment (Vercel)

1. Push to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy — adapter-auto handles SQLite on Vercel (uses `@vercel/kysely`)

## Known Limitations

- SQLite doesn't support concurrent writes well — use for low-traffic apps
- No built-in migrations in production — use Prisma/Drizzle for complex schemas
- WebSockets not supported — use Server-Sent Events for real-time

## Useful Commands

```bash
# Reset database
rm -f data/app.db && npm run db:migrate && npm run db:seed

# View database
sqlite3 data/app.db ".schema"

# Generate types from DB
npx kysely-codegen --out-file ./types/db.ts
```

## Contributing

- Follow existing file structure
- Use Kysely for all queries (no raw SQL except migrations)
- Add TypeScript types for all API responses
- Test against local SQLite before submitting PR