# CLAUDE.md — Next.js 15 + SQLite SaaS

> This file gives Claude Code full context to work on this project without asking clarifying questions.

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.x |
| Runtime | Node.js | 20+ |
| Language | TypeScript | 5.x (strict mode) |
| Database | SQLite via better-sqlite3 | 11.x |
| Migrations | Custom SQL files | — |
| ORM | None — raw SQL with typed helpers | — |
| Styling | Tailwind CSS | 4.x |
| Auth | Custom session cookies (no NextAuth) | — |
| Payments | Stripe Checkout + Webhooks | — |
| Deployment | Docker → any VPS / Railway / Fly.io | — |

## Project Structure

```
├── app/
│   ├── (auth)/           # Auth routes (login, register, forgot-password)
│   ├── (dashboard)/      # Authenticated routes
│   │   ├── layout.tsx    # Dashboard shell with sidebar + auth guard
│   │   ├── page.tsx      # Dashboard home
│   │   └── settings/     # User settings
│   ├── (marketing)/      # Public pages (landing, pricing, blog)
│   ├── api/
│   │   ├── webhooks/     # Stripe webhooks, etc.
│   │   └── v1/           # Public API routes (if any)
│   ├── layout.tsx        # Root layout
│   └── globals.css
├── components/
│   ├── ui/               # Primitives (Button, Input, Card, Modal)
│   └── features/         # Domain components (PricingTable, UserMenu)
├── db/
│   ├── index.ts          # Database singleton + query helpers
│   ├── schema.ts         # TypeScript types matching SQL tables
│   └── migrations/       # Numbered SQL files: 001_init.sql, 002_add_teams.sql
├── lib/
│   ├── auth.ts           # Session management (cookie-based)
│   ├── stripe.ts         # Stripe client + helpers
│   ├── email.ts          # Transactional email sender
│   └── utils.ts          # Shared utilities
├── scripts/
│   ├── migrate.ts        # Run pending migrations
│   └── seed.ts           # Dev seed data
├── public/
├── data/                 # SQLite database file lives here (gitignored)
│   └── app.db
├── CLAUDE.md             # ← You are here
├── .env.local            # Local env vars (never committed)
└── package.json
```

## Dev Commands

```bash
npm run dev              # Start dev server (port 3000)
npm run build            # Production build
npm run start            # Start production server
npm run migrate          # Run pending SQL migrations
npm run seed             # Seed dev database
npm run typecheck        # tsc --noEmit
npm run lint             # ESLint + Prettier check
npm run test             # Vitest
```

## Database Rules

### SQLite is the production database. Not Postgres. Not "for now."

We chose SQLite because:
- Single-file deployment — no database server to manage
- WAL mode gives us concurrent reads with single-writer performance
- For a SaaS under 10K users, SQLite outperforms Postgres (zero network latency)

### Migration conventions

1. Migrations are **numbered SQL files** in `db/migrations/`: `001_init.sql`, `002_add_teams.sql`
2. Each file runs inside a **transaction** (the migrate script wraps it)
3. **Never modify an existing migration.** Create a new one.
4. **Always include `IF NOT EXISTS`** for `CREATE TABLE` / `CREATE INDEX`
5. Use `STRICT` mode on all tables: `CREATE TABLE users (...) STRICT`
6. Every table has: `id INTEGER PRIMARY KEY`, `created_at TEXT NOT NULL DEFAULT (datetime('now'))`, `updated_at TEXT`

### Query patterns

```typescript
// ✅ Do this — typed query helpers in db/index.ts
import { db } from '@/db';
const user = db.get<User>('SELECT * FROM users WHERE id = ?', [userId]);

// ✅ Parameterized queries ALWAYS
db.run('INSERT INTO users (email, name) VALUES (?, ?)', [email, name]);

// ❌ Never string interpolation
db.run(`INSERT INTO users (email) VALUES ('${email}')`);  // SQL INJECTION

// ❌ Never use an ORM
import { prisma } from '...';  // NO. We use raw SQL.
```

### Schema types

Every table has a matching TypeScript type in `db/schema.ts`:

```typescript
// db/schema.ts
export interface User {
  id: number;
  email: string;
  name: string;
  password_hash: string;
  stripe_customer_id: string | null;
  plan: 'free' | 'pro' | 'team';
  created_at: string;
  updated_at: string | null;
}
```

Update `schema.ts` whenever you modify a migration. They must stay in sync.

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files & folders | kebab-case | `user-settings.tsx` |
| Components | PascalCase | `UserSettings` |
| Functions | camelCase | `getUserById` |
| DB columns | snake_case | `stripe_customer_id` |
| DB tables | plural snake_case | `users`, `team_members` |
| Env vars | SCREAMING_SNAKE | `STRIPE_SECRET_KEY` |
| API routes | kebab-case URLs | `/api/v1/team-members` |
| Migrations | numbered + snake_case | `003_add_stripe_fields.sql` |

## Component Patterns

### Server Components (default)

Every component is a Server Component unless it needs interactivity. This means:
- No `"use client"` unless the component uses `useState`, `useEffect`, event handlers, or browser APIs
- Data fetching happens in the component (no API calls from Server Components — query the DB directly)
- Pass data down to Client Components as props

### Client Components

```typescript
"use client";  // First line, always

// ✅ Minimal client components — only the interactive part
export function LikeButton({ postId }: { postId: number }) {
  const [liked, setLiked] = useState(false);
  // ...
}

// ❌ Don't make entire pages client components
"use client";
export default function DashboardPage() { ... }  // NO
```

### Server Actions

```typescript
// ✅ Define in a separate file or inline with "use server"
"use server";

export async function updateProfile(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error("Unauthorized");
  
  const name = formData.get("name") as string;
  db.run("UPDATE users SET name = ?, updated_at = datetime('now') WHERE id = ?", 
    [name, session.userId]);
  
  revalidatePath("/dashboard/settings");
}
```

### Error handling

- Server Actions throw errors → caught by `error.tsx` boundaries
- API routes return proper HTTP status codes + JSON `{ error: string }`
- Never swallow errors silently. Log them. Surface them.

## Auth Pattern

Cookie-based sessions. No JWT. No NextAuth.

```typescript
// lib/auth.ts
export async function getSession(): Promise<Session | null> {
  const cookie = cookies().get('session');
  if (!cookie) return null;
  return db.get<Session>(
    'SELECT * FROM sessions WHERE token = ? AND expires_at > datetime("now")',
    [cookie.value]
  );
}
```

- Sessions stored in `sessions` table (token, user_id, expires_at)
- Middleware checks auth for `/dashboard/*` routes
- Password hashing: `bcrypt` with cost factor 12

## What We Don't Do (and Why)

| Anti-pattern | Why not |
|-------------|---------|
| Prisma / Drizzle / any ORM | Adds abstraction over simple SQL. SQLite queries are straightforward. ORMs hide performance issues. |
| NextAuth / Auth.js | Over-engineered for our needs. Cookie + session table = 50 lines of code. |
| `"use client"` on pages | Kills SSR benefits. Only interactive leaf components should be client. |
| Separate backend API | Next.js API routes + Server Actions handle everything. No Express/Fastify. |
| `.env` files in git | Security risk. Use `.env.local` (gitignored) + deployment env vars. |
| `any` type | TypeScript strict mode is on. Fix the type, don't escape it. |
| Barrel exports (`index.ts`) | Breaks tree-shaking, slows builds. Import from specific files. |
| CSS Modules | Tailwind handles styling. One approach, not two. |
| `useEffect` for data fetching | Server Components fetch data. Client Components receive it as props. |
| Global state (Redux, Zustand) | Server Components + React context covers 99% of cases. |

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_PATH=./data/app.db
SESSION_SECRET=<random-64-chars>
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
SMTP_HOST=smtp.resend.com
SMTP_API_KEY=re_...
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Rules:
- `NEXT_PUBLIC_*` = exposed to browser. Never put secrets here.
- All other env vars = server-only.
- Fail fast: if a required env var is missing, throw at startup (check in `lib/env.ts`).

## Testing

- **Unit tests**: Vitest for utility functions and DB queries
- **Integration**: Test Server Actions by calling them directly
- **No E2E in CI** (too slow). Run Playwright locally before major releases.

```bash
npm run test              # Run all tests
npm run test -- --watch   # Watch mode
```

Test files live next to the code: `lib/auth.test.ts`, `db/index.test.ts`.

## Deployment

```bash
docker build -t app .
docker run -v ./data:/app/data -p 3000:3000 app
```

The `Dockerfile` uses multi-stage builds:
1. `deps` stage: install node_modules
2. `build` stage: `next build`
3. `run` stage: minimal image with `next start`

SQLite data directory (`/app/data`) is a mounted volume — persists across deployments.

## When in Doubt

1. **Keep it simple.** If a solution needs a new dependency, look for a stdlib/built-in way first.
2. **Read the existing code.** This project has patterns — follow them.
3. **SQL is fine.** Don't abstract it. Write the query. Type the result.
4. **Server Components first.** `"use client"` is the escape hatch, not the default.
5. **Ship it.** Perfect is the enemy of deployed.
