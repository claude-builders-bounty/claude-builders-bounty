# CLAUDE.md — Next.js + SQLite SaaS Starter

## Project Overview

A lightweight SaaS starter using Next.js 14 (App Router), SQLite (via better-sqlite3), and Tailwind CSS. Built for rapid prototyping with auth, billing, and admin dashboards out of the box.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 14 (App Router) |
| Database | SQLite + better-sqlite3 |
| Auth | NextAuth.js v5 (beta) |
| Styling | Tailwind CSS + shadcn/ui |
| Payments | Stripe |
| Email | Resend |
| Validation | Zod |

## Project Structure

```
├── app/
│   ├── (auth)/           # Auth routes (login, register)
│   ├── (dashboard)/      # Protected SaaS routes
│   ├── api/              # API routes
│   └── layout.tsx        # Root layout
├── components/ui/        # shadcn components
├── lib/
│   ├── db.ts            # SQLite connection + helpers
│   ├── auth.ts          # NextAuth config
│   └── stripe.ts        # Stripe helpers
├── prisma/              # (optional) schema if migrating to Prisma
└── scripts/
    └── seed.ts          # Database seeding
```

## Database Schema (SQLite)

```sql
-- Users (managed by NextAuth)
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  image TEXT,
  role TEXT DEFAULT 'user', -- user | admin
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  subscription_status TEXT DEFAULT 'inactive',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Teams (multi-tenancy)
CREATE TABLE teams (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  owner_id TEXT NOT NULL REFERENCES users(id),
  stripe_customer_id TEXT,
  plan TEXT DEFAULT 'free', -- free | pro | enterprise
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Team Members
CREATE TABLE team_members (
  team_id TEXT REFERENCES teams(id),
  user_id TEXT REFERENCES users(id),
  role TEXT DEFAULT 'member', -- owner | admin | member
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (team_id, user_id)
);

-- API Keys
CREATE TABLE api_keys (
  id TEXT PRIMARY KEY,
  team_id TEXT REFERENCES teams(id),
  name TEXT,
  key_hash TEXT NOT NULL,
  last_used_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  revoked_at DATETIME
);

-- Audit Logs
CREATE TABLE audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  team_id TEXT REFERENCES teams(id),
  user_id TEXT REFERENCES users(id),
  action TEXT NOT NULL,
  resource TEXT,
  metadata TEXT, -- JSON
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Key Conventions

1. **Database**: Use `lib/db.ts` for all SQL. Never import `better-sqlite3` directly in components.
2. **Auth**: Server Components use `auth()` from `lib/auth.ts`. Client Components use `useSession()`.
3. **API Keys**: Always hash with `bcrypt` before storage. Display the raw key only once on creation.
4. **Billing**: Webhook handler at `app/api/webhooks/stripe/route.ts`. Idempotent processing required.
5. **Audit**: Every mutating action must write to `audit_logs`.

## Critical Rules

- Never expose `api_keys.key_hash` in API responses — only return the key name and metadata.
- All admin routes must check `user.role === 'admin'` before rendering.
- Stripe webhook must verify the signature with `stripe.webhooks.constructEvent()`.
- SQLite connection is singleton — reuse the same `Database` instance.
- Use transactions for multi-table writes (e.g., creating a team + adding owner as member).

## Environment Variables

```bash
# Required
DATABASE_URL="file:./dev.db"
NEXTAUTH_SECRET="random-string-here"
NEXTAUTH_URL="http://localhost:3000"

# OAuth (pick at least one)
GITHUB_CLIENT_ID=""
GITHUB_CLIENT_SECRET=""
GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""

# Stripe
STRIPE_PUBLISHABLE_KEY=""
STRIPE_SECRET_KEY=""
STRIPE_WEBHOOK_SECRET=""

# Email
RESEND_API_KEY=""
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server |
| `npm run db:seed` | Seed database |
| `npm run db:migrate` | Run migrations |
| `npm run db:studio` | Open Drizzle Studio |
| `npm run stripe:listen` | Forward webhooks locally |

## Testing Strategy

- **Unit**: Vitest for utility functions and Zod schemas.
- **Integration**: Playwright for auth flows and critical user paths.
- **Database**: Each test gets a fresh SQLite `:memory:` instance.
