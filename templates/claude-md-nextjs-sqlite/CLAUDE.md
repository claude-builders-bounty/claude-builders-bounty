# CLAUDE.md - Next.js 15 + SQLite SaaS Project

This file provides guidance to Claude Code when working with this codebase.

## Project Overview

SaaS application built with Next.js 15 App Router and SQLite (better-sqlite3).

## Architecture

### Tech Stack
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via better-sqlite3
- **Styling**: Tailwind CSS
- **Authentication**: NextAuth.js v5
- **Payments**: Stripe

### Folder Structure
```
src/
├── app/                    # App Router pages
│   ├── (auth)/             # Auth route group (login, signup)
│   ├── (dashboard)/        # Dashboard route group
│   ├── api/                # API routes
│   │   ├── auth/[...nextauth]/route.ts
│   │   ├── stripe/webhooks/route.ts
│   │   └── trpc/[trpc]/route.ts
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Reusable UI components
│   ├── forms/              # Form components
│   └── layout/             # Layout components (header, footer, sidebar)
├── lib/
│   ├── db/                 # Database layer
│   │   ├── index.ts        # Database connection & config
│   │   ├── schema.ts       # Table definitions
│   │   └── migrations/     # Numbered migration files
│   ├── auth.ts             # Auth configuration
│   ├── stripe.ts           # Stripe client
│   └── utils.ts            # Utility functions
├── server/
│   ├── actions/            # Server Actions
│   └── trpc/               # tRPC router & procedures
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript type definitions
└── styles/                 # Global styles
```

## Database

### Connection
```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import path from 'path';

const dbPath = path.join(process.cwd(), 'data', 'app.db');
export const db = new Database(dbPath);

// Enable WAL mode for better concurrent read performance
db.pragma('journal_mode = WAL');
// Enable foreign keys
db.pragma('foreign_keys = ON');
```

### Migrations
- Located in `lib/db/migrations/`
- Numbered format: `001_initial.sql`, `002_add_users_table.sql`
- Forward-only, idempotent (use `IF NOT EXISTS`)
- Run with: `npx tsx lib/db/migrate.ts`

### Schema Conventions
- Use `INTEGER PRIMARY KEY AUTOINCREMENT` for IDs
- Use `TEXT` for strings, `INTEGER` for booleans (0/1)
- Use `DATETIME DEFAULT CURRENT_TIMESTAMP` for created_at
- Always include `updated_at` with trigger or application-level update
- Foreign keys: `REFERENCES table(id) ON DELETE CASCADE`

### Query Patterns
```typescript
// ALWAYS use prepared statements
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(userId);

// For inserts
const insert = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
const result = insert.run(email, name);

// For transactions
const transfer = db.transaction((from, to, amount) => {
  db.prepare('UPDATE accounts SET balance = balance - ? WHERE id = ?').run(amount, from);
  db.prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?').run(amount, to);
});
```

## Server Components & Actions

### Server Components (Default)
- All components are Server Components by default
- Use `'use client'` directive only when needed (interactivity, browser APIs)
- Data fetching happens in the component directly

### Server Actions
- Place in `server/actions/`
- Always use `'use server'` directive
- Validate input with Zod before database operations
- Return typed responses

```typescript
// server/actions/user.ts
'use server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function createUser(formData: FormData) {
  const validated = CreateUserSchema.parse({
    email: formData.get('email'),
    name: formData.get('name'),
  });

  const stmt = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
  const result = stmt.run(validated.email, validated.name);

  revalidatePath('/dashboard/users');
  redirect('/dashboard/users');
}
```

## API Routes

### Pattern
- Use Next.js Route Handlers in `app/api/`
- For tRPC: `app/api/trpc/[trpc]/route.ts`
- For webhooks: `app/api/stripe/webhooks/route.ts`
- Always validate webhook signatures

### Stripe Webhooks
```typescript
// app/api/stripe/webhooks/route.ts
import Stripe from 'stripe';
import { headers } from 'next/headers';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  const body = await req.text();
  const headersList = headers();
  const sig = headersList.get('stripe-signature')!;

  const event = stripe.webhooks.constructEvent(
    body, sig, process.env.STRIPE_WEBHOOK_SECRET!
  );

  switch (event.type) {
    case 'checkout.session.completed':
      // Handle successful checkout
      break;
    case 'customer.subscription.updated':
      // Handle subscription changes
      break;
  }

  return new Response('OK', { status: 200 });
}
```

## Authentication

### NextAuth v5 Setup
```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { db } from './db';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      authorize: async (credentials) => {
        // Verify against SQLite
        const user = db.prepare('SELECT * FROM users WHERE email = ?')
          .get(credentials.email);
        if (!user) return null;
        // Verify password with bcrypt
        const valid = await bcrypt.compare(credentials.password, user.password_hash);
        return valid ? { id: user.id, email: user.email, name: user.name } : null;
      },
    }),
  ],
  callbacks: {
    session: async ({ session, token }) => {
      session.user.id = token.sub;
      return session;
    },
  },
});
```

## Environment Variables
```
DATABASE_URL=./data/app.db
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Development Commands
```bash
# Install dependencies
npm install

# Run migrations
npx tsx lib/db/migrate.ts

# Dev server
npm run dev

# Build
npm run build

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

## Security Rules
- NEVER trust client input - always validate with Zod
- ALWAYS use prepared statements for SQL queries
- NEVER store secrets in code - use environment variables
- ALWAYS verify Stripe webhook signatures
- NEVER expose database errors to the client
- ALWAYS use HTTPS in production
- NEVER log sensitive data (passwords, tokens, PII)

## Testing
- Unit tests: `*.test.ts` alongside source files
- Integration tests: `__tests__/` directory
- Use `vitest` as test runner
- Test database: use in-memory SQLite for tests

## Common Patterns

### Pagination
```typescript
const PAGE_SIZE = 20;
const page = parseInt(searchParams.page || '1');
const offset = (page - 1) * PAGE_SIZE;

const items = db.prepare(
  'SELECT * FROM items ORDER BY created_at DESC LIMIT ? OFFSET ?'
).all(PAGE_SIZE, offset);

const total = db.prepare('SELECT COUNT(*) as count FROM items').get();
const totalPages = Math.ceil(total.count / PAGE_SIZE);
```

### Soft Deletes
```typescript
// Instead of DELETE, set deleted_at
db.prepare('UPDATE items SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?').run(id);
// Queries should always filter: WHERE deleted_at IS NULL
```
