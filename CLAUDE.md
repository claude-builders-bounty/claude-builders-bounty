# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project context for Claude Code. Drop this in your project root and Claude will understand your stack, conventions, and what to avoid — no clarification needed.

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components, streaming, PPR |
| Language | TypeScript | 5.x | strict: true, no `any` |
| Database | Turso (libsql) / better-sqlite3 | latest | Serverless-first SQLite with replication |
| ORM | Drizzle ORM | 0.40+ | SQL-like API, composable, zero runtime overhead |
| Auth | Lucid (or NextAuth v5) | latest | DB-backed sessions, no vendor lock-in |
| Validation | Zod | 3.x | Runtime + type inference; single source of truth |
| Styling | Tailwind CSS v4 | 4.x | Utility-first, CSS-first config |
| UI Components | shadcn/ui | latest | Radix primitives, unstyled, copy-paste |
| Forms | React Aria Components / @react-aria | latest | Accessible, headless, RSC-safe |
| Testing | Vitest + Playwright | 2.x / latest | Fast, ESM-native, E2E |
| Payments | Stripe (optional) | latest | Webhooks + Checkout |
| Hosting | Vercel (preferred) or Docker | — | Edge-ready, zero-config deploys |

## Folder Structure

```
src/
├── app/                         # Next.js App Router
│   ├── (marketing)/            # Public pages (landing, pricing, blog)
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── (auth)/                 # Auth route group (login, register, forgot-password)
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx          # Auth page shell (no sidebar)
│   ├── (dashboard)/            # Protected routes (requires session)
│   │   ├── layout.tsx          # Dashboard shell: sidebar + auth check
│   │   ├── page.tsx            # Dashboard overview
│   │   ├── settings/
│   │   └── projects/
│   ├── api/                    # Route handlers
│   │   ├── webhooks/           # Stripe, external service webhooks
│   │   ├── trpc/              # (optional) tRPC endpoints
│   │   └── [...route]/        # Generic REST handlers
│   ├── layout.tsx              # Root layout (fonts, metadata, providers)
│   ├── page.tsx                # Landing page
│   ├── not-found.tsx           # 404 page
│   ├── error.tsx               # Global error boundary
│   ├── global-error.tsx        # Root error boundary (catches layout errors)
│   └── loading.tsx             # Global loading fallback
├── lib/
│   ├── db/
│   │   ├── index.ts            # DB connection singleton
│   │   ├── schema/             # Drizzle schema files (one per domain)
│   │   │   ├── users.ts
│   │   │   ├── projects.ts
│   │   │   └── subscriptions.ts
│   │   ├── queries/            # Reusable query functions
│   │   │   ├── users.ts
│   │   │   └── projects.ts
│   │   ├── migrations/         # Generated SQL migrations
│   │   └── seed.ts             # Development seed script
│   ├── auth/                   # Auth configuration
│   │   ├── index.ts            # Auth provider config
│   │   ├── middleware.ts       # Session helpers
│   │   └── actions.ts          # Auth server actions (login, register, logout)
│   ├── validation/             # Zod schemas (mirrors DB schema)
│   │   ├── auth.ts
│   │   └── project.ts
│   ├── email/                  # Email templates + send helpers
│   ├── payments/               # Stripe helpers
│   └── utils.ts                # Shared utilities (cn(), formatDate, etc.)
├── components/
│   ├── ui/                     # Primitive UI (shadcn/ui)
│   ├── forms/                  # Form components + fields
│   ├── layout/                 # Sidebar, header, nav
│   └── features/               # Feature-specific compositions
├── hooks/                      # Shared React hooks
├── actions/                    # Server Actions (domain-organized)
│   ├── auth.ts
│   └── projects.ts
├── styles/
│   └── globals.css             # Tailwind entry + CSS variables
├── middleware.ts               # Auth middleware
└── instrumentation.ts          # Telemetry / monitoring setup (Node.js only)
```

## Commands

```bash
# Development
npm run dev              # Start dev server (localhost:3000)
npm run dev:turbo        # Start with Turbopack (faster HMR)

# Database
npm run db:generate      # Generate migration from schema changes
npm run db:migrate       # Run pending migrations
npm run db:push          # Push schema directly (dev only — skips migration files)
npm run db:studio        # Drizzle Studio web UI (DB browser)
npm run db:seed          # Seed development data
npm run db:reset         # Drop + recreate + migrate + seed

# Build & Deploy
npm run build            # Production build
npm run start            # Start production server
npm run lint             # ESLint + TypeScript checks
npm run typecheck        # tsc --noEmit

# Testing
npm run test             # Vitest (unit + integration)
npm run test:watch       # Watch mode
npm run test:e2e         # Playwright E2E tests
npm run test:coverage    # Coverage report

# Utilities
npm run format           # Prettier
npm run format:check     # Check formatting in CI
```

## Database Rules

### Schema Is the Source of Truth

**NEVER write raw SQL migrations by hand.** Always:

1. Edit `src/lib/db/schema/<domain>.ts`
2. Run `npm run db:generate` → review generated SQL
3. Run `npm run db:migrate` (or `npm run db:push` in early dev)

```typescript
// ✅ DO: Define everything in Drizzle schema
import { sqliteTable, text, integer, uniqueIndex } from "drizzle-orm/sqlite-core";

export const users = sqliteTable(
  "users",
  {
    id: text("id").primaryKey(),
    email: text("email").notNull(),
    name: text("name"),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .defaultNow(),
  },
  (table) => ({
    emailIdx: uniqueIndex("users_email_idx").on(table.email),
  }),
);
```

### Migration Conventions

- One migration per schema change (squash if multiple changes in same PR)
- Migration files are **immutable** — never edit a committed migration
- Name format: `0001_tame_beach.sql` (auto-generated by Drizzle Kit)
- Always review generated SQL before committing:
  ```sql
  -- ✅ Good: explicit, generated by Drizzle
  CREATE TABLE users (
    id text PRIMARY KEY NOT NULL,
    email text NOT NULL,
    name text
  );
  CREATE UNIQUE INDEX users_email_idx ON users(email);
  ```
- Rollback: `drizzle-kit drop` OR restore previous migration + generate
- ⚠️ Never `db:push` on production — it bypasses migration tracking

### Query Patterns

```typescript
// ✅ DO: Drizzle query builder (type-safe, composable)
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema/users";
import { eq, and, gte, desc } from "drizzle-orm";

const result = await db
  .select()
  .from(users)
  .where(and(eq(users.plan, "pro"), gte(users.createdAt, cutoffDate)))
  .orderBy(desc(users.createdAt))
  .limit(10);

// ✅ DO: Prepared statements for parameterized queries
const getUserByEmail = db
  .select()
  .from(users)
  .where(eq(users.email, sql.placeholder("email")))
  .prepare("get_user_by_email");

const user = await getUserByEmail.execute({ email: "a@b.com" });

// ❌ DON'T: Raw SQL strings (type-unsafe, injection-prone)
const user = await db.run(sql`SELECT * FROM users WHERE email = ${email}`);
```

### Transactions

```typescript
import { db } from "@/lib/db";

// ✅ DO: Use db.transaction for atomic operations
await db.transaction(async (tx) => {
  const [org] = await tx.insert(organizations).values({ name }).returning();
  await tx.insert(members).values({ userId: user.id, orgId: org.id });
});

// ❌ DON'T: Sequential inserts without rollback
await db.insert(organizations).values({ name });  // inserts even if next fails
await db.insert(members).values({ userId, orgId });  // can fail independently
```

### Connection Management

| Environment | Strategy | Why |
|-------------|----------|-----|
| Development | File DB (`./data/dev.db`) | Editable, inspectable |
| Test | `:memory:` | Fast, isolated, auto-cleanup |
| Production (Vercel) | Turso (libsql) | HTTP-based, serverless-friendly |
| Production (Docker) | better-sqlite3 + volume mount | Single-process, simple |


## Component Patterns

### Server Components (Default)

```typescript
// ✅ DO: Server Component — default, no "use client"
export default async function ProjectList({ userId }: { userId: string }) {
  const projects = await db
    .select()
    .from(projects)
    .where(eq(projects.ownerId, userId));

  return (
    <ul>
      {projects.map((p) => (
        <li key={p.id}>{p.name}</li>
      ))}
    </ul>
  );
}
```

### Client Components (Only When Needed)

```typescript
// ✅ DO: 'use client' only for interactivity
"use client";
import { useState } from "react";

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button onClick={() => navigator.clipboard.writeText(text).then(() => setCopied(true))}>
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}
```

### What We Don't Do In Components

| ❌ Anti-Pattern | ✅ Instead |
|----------------|-----------|
| Data fetching in Client Components | Server Components or Server Actions |
| `useEffect` for data fetching | Server Components or `useActionState` |
| Global state (Redux / Zustand) | Server Components + URL state + `useActionState` |
| CSS Modules / styled-components | Tailwind utility classes |
| `any` types | Zod inference or explicit types |
| `JSON.parse(JSON.stringify(x))` | Drizzle `.$type()` for complex fields |
| Magic strings for routes | `route.ts` exports or constants file |

### Forms Pattern

```typescript
// ✅ DO: Server Actions with useActionState
"use client";
import { useActionState } from "react";
import { createProject } from "@/actions/projects";

export function CreateProjectForm() {
  const [state, formAction, pending] = useActionState(createProject, { errors: {} });

  return (
    <form action={formAction}>
      <input name="name" required />
      {state.errors?.name && <p className="text-red-500">{state.errors.name}</p>}
      <button type="submit" disabled={pending}>
        {pending ? "Creating..." : "Create Project"}
      </button>
    </form>
  );
}
```

```typescript
// Server Action with validation
"use server";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function createProject(prev: any, formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { errors: parsed.error.flatten().fieldErrors };

  const project = await db.insert(projectsTable).values(parsed.data).returning();
  revalidatePath("/dashboard");
  return { success: true, project: project[0] };
}
```

## Auth Patterns

### Session Management

```typescript
// ✅ DO: Session in DB, cookie-based
import { cookies } from "next/headers";

export async function getSession() {
  const sessionId = (await cookies()).get("session_id")?.value;
  if (!sessionId) return null;
  const [session] = await db.select().from(sessions).where(eq(sessions.id, sessionId));
  return session ?? null;
}
```

### Middleware Protection

```typescript
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const sessionId = request.cookies.get("session_id")?.value;
  const isDashboard = request.nextUrl.pathname.startsWith("/dashboard");

  if (isDashboard && !sessionId) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)"],
};
```

### Anti-Patterns

| ❌ Avoid | Why |
|----------|-----|
| Storing tokens in localStorage | XSS-vulnerable |
| JWT without rotation | No revocation possible |
| Client-side session checks | Can be bypassed |
| Password in DB (plaintext or weak hash) | Use OAuth or magic links |

## Server Actions

### Structure

```typescript
// actions/projects.ts — domain-organized server actions
"use server";

import { z } from "zod";
import { db } from "@/lib/db";
import { projectsTable } from "@/lib/db/schema/projects";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";

// Always validate input, check auth, return typed result
export async function deleteProject(id: string) {
  const session = await getSession();
  if (!session) throw new Error("Unauthorized");

  await db.delete(projectsTable).where(eq(projectsTable.id, id));
  revalidatePath("/dashboard");
  redirect("/dashboard");
}
```

### Caching & Revalidation

```typescript
// ✅ Revalidate specific paths after mutations
revalidatePath("/dashboard");                     // one page
revalidatePath("/dashboard", "layout");            // entire route group
revalidateTag("projects");                         // tagged fetch

// ✅ Use fetch cache tags in Server Components
export async function getProjects() {
  const projects = await db.select().from(projectsTable);
  return projects;
}

export default async function Dashboard() {
  unstable_cacheTag("projects");
  const projects = await getProjects();
  // ...
}
```

## Error Handling

### Error Boundaries

```typescript
// app/error.tsx — Client-side error boundary for a route segment
"use client";
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

```typescript
// app/global-error.tsx — Catches root layout errors
"use client";
export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <html>
      <body>
        <h2>Fatal error</h2>
        <button onClick={reset}>Reload</button>
      </body>
    </html>
  );
}
```

### API Error Responses

```typescript
// app/api/[[...route]]/route.ts
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");
    if (!id) {
      return Response.json({ error: "Missing id" }, { status: 400 });
    }
    // ... query
    return Response.json({ data });
  } catch (error) {
    console.error("API error:", error);
    return Response.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
```

## API Patterns

### Route Handlers

```typescript
// ✅ DO: Route handlers with typed responses
export async function GET(request: Request) {
  const session = await getSession();
  if (!session) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }
  const data = await getProjectsForUser(session.userId);
  return Response.json({ data });
}

export async function POST(request: Request) {
  const body = await request.json();
  const parsed = createProjectSchema.safeParse(body);
  if (!parsed.success) {
    return Response.json({ errors: parsed.error.flatten() }, { status: 422 });
  }
  const [project] = await db.insert(projectsTable).values(parsed.data).returning();
  return Response.json({ data: project }, { status: 201 });
}
```

### Pagination (Cursor-based)

```typescript
// ✅ DO: Cursor-based pagination (stable across inserts)
export async function getProjects(cursor?: string, limit = 20) {
  const results = await db
    .select()
    .from(projectsTable)
    .where(cursor ? lt(projectsTable.id, cursor) : undefined)
    .orderBy(desc(projectsTable.createdAt))
    .limit(limit + 1);

  const hasMore = results.length > limit;
  return {
    data: results.slice(0, limit),
    nextCursor: hasMore ? results[limit - 1].id : null,
  };
}
```

### Rate Limiting

```typescript
// ✅ DO: Simple rate limiting for API routes
import { RateLimiter } from "@/lib/rate-limit";

const limiter = new RateLimiter({ tokensPerInterval: 10, interval: "minute" });

export async function POST(request: Request) {
  const ip = request.headers.get("x-forwarded-for") ?? "unknown";
  if (!(await limiter.check(ip))) {
    return Response.json({ error: "Too many requests" }, { status: 429 });
  }
  // ... handle request
}
```

## Testing

```typescript
// ✅ Unit test: pure function
import { describe, it, expect } from "vitest";
import { formatCurrency } from "@/lib/utils";

describe("formatCurrency", () => {
  it("formats USD correctly", () => {
    expect(formatCurrency(10.5, "USD")).toBe("$10.50");
  });
});

// ✅ Integration test: DB operations
import { db } from "@/lib/db";
import { usersTable } from "@/lib/db/schema/users";

describe("User queries", () => {
  it("creates and retrieves a user", async () => {
    const [user] = await db.insert(usersTable).values({ email: "test@test.com" }).returning();
    expect(user.email).toBe("test@test.com");
  });
});
```

### Test Database

- Use `:memory:` SQLite for tests (fast, isolated)
- Run `db:push` before test suite, reset between test files
- No mocking of DB functions — test against real SQLite
- No MSW — test API handlers with actual request/response

## Background Jobs

```typescript
// ✅ DO: Use a simple job queue with SQLite
// lib/jobs.ts
export async function enqueueJob(type: string, payload: unknown) {
  await db.insert(jobs).values({ type, payload: JSON.stringify(payload), status: "pending" });
}

// Script: scripts/worker.ts — called by cron
// Cron schedule: every 5 minutes on Vercel, systemd timer on Docker
```

## Environment Variables

```bash
# .env.example — DO NOT commit .env
DATABASE_URL=file:./data/dev.db    # Turso: libsql://<db>.turso.io
AUTH_SECRET=***                    # Session encryption key
NEXT_PUBLIC_APP_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_***
STRIPE_WEBHOOK_SECRET=whsec_***
RESEND_API_KEY=re_***              # Email (optional)
```

- All env vars: `process.env.VAR` (no `NEXT_PUBLIC_` prefix unless exposed to client bundle)
- Never commit `.env` — only `.env.example`
- Validate required vars at startup in `instrumentation.ts` or `lib/config.ts`

## Anti-Patterns (Don't Do This)

| Anti-Pattern | Why | Instead |
|-------------|-----|---------|
| Prisma | Heavy binary, slow cold start, vendor DSL | Drizzle (SQL-like, zero runtime overhead) |
| next-auth v4 | Complex callbacks, magic strings | Lucid or NextAuth v5 (simpler API) |
| `useState` for all forms | Excessive client state | Server Actions + `useActionState` |
| `getServerSideProps` | Pages Router legacy | App Router `async` components |
| `revalidate` without tags | Over-revalidation | `revalidateTag("projects")` |
| Hardcoded DB path | Breaks in different envs | `DATABASE_URL` env var always |
| Manual `JSON.stringify` for API | No type safety | Zod + `Response.json()` |
| `useEffect` + `fetch` for data | Waterfall, no RSC benefits | Server Components or `server-only` |
| Large client bundles | Slow FCP | `next/dynamic` for heavy client libs |
| Catching all errors silently | Debugging hell | Structured error logging |
| Multiple DB connections in serverless | Connection exhaustion | Singleton pattern or connection pooling |
| Dynamic imports everywhere | Defeats RSC | Static imports; dynamic only for heavy client libs |

## Security Checklist

- ✅ SQL injection: prevented by Drizzle parameterized queries
- ✅ XSS: prevented by React's default escaping
- ✅ CSRF: Server Actions + SameSite cookies
- ✅ Rate limiting on auth routes and API endpoints
- ✅ Input validation: Zod on every user-facing input
- ✅ Session rotation on login / privilege escalation
- ✅ `x-powered-by: Next.js` removed in production
- ✅ CSP headers set in `next.config.js`
- ✅ No secrets in client bundle (no `NEXT_PUBLIC_` for secrets)

## Deployment

### Vercel (Preferred)

```bash
# vercel.json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm install"
}
```

- Turso DB for edge-compatible SQLite (HTTP protocol)
- Serverless functions handle DB connections via Turso's HTTP client
- No cold-start issues with Drizzle + Turso

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
```

- Single-process — scale horizontally behind a load balancer
- better-sqlite3 with mounted volume for persistence
- Health check: `HEALTHCHECK --interval=30s CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1`
