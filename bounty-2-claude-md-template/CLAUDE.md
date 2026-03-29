# CLAUDE.md — Next.js 15 + SQLite SaaS

> This file is the single source of truth for Claude Code working in this codebase.
> Every rule is opinionated and earned from production experience. No generic advice.

## Stack (Pinned Versions)

| Package | Version | Why This Version |
|---------|---------|------------------|
| next | 15.x | App Router stable, Server Actions GA, Turbopack default |
| react | 19.x | `use()` hook, Server Components, Actions |
| typescript | 5.7+ | `satisfies`, `const` type params, decorator metadata |
| better-sqlite3 | 11.x | Synchronous API matches Server Components — no async overhead |
| drizzle-orm | 0.38+ | Type-safe SQL, zero runtime overhead, SQLite-native |
| drizzle-kit | 0.30+ | Migration generation, `drizzle-kit push` for dev |
| zod | 3.24+ | Schema validation for forms, API input, env vars |
| tailwindcss | 4.x | CSS-first config, automatic content detection |
| lucia | 3.x | Session-based auth built for SQLite, no JWT bloat |

**Runtime:** Node.js 20 LTS (required for `--experimental-sqlite` node:sqlite fallback).
**Package manager:** pnpm (strict, fast, disk-efficient). Lock file is `pnpm-lock.yaml`.

## Dev Commands

```bash
pnpm dev                  # Start dev server (Turbopack) at localhost:3000
pnpm build                # Production build — fails on type errors (strict)
pnpm start                # Start production server
pnpm lint                 # ESLint + Prettier check (no auto-fix)
pnpm lint:fix             # ESLint + Prettier auto-fix
pnpm typecheck            # tsc --noEmit — run before every commit
pnpm test                 # Vitest unit + integration tests
pnpm test:watch           # Vitest in watch mode
pnpm test:coverage        # Vitest with c8 coverage (target: 80%)
pnpm test:e2e             # Playwright E2E tests
pnpm db:generate          # drizzle-kit generate — create migration SQL from schema changes
pnpm db:migrate           # drizzle-kit migrate — apply pending migrations
pnpm db:push              # drizzle-kit push — sync schema directly (dev only, never prod)
pnpm db:studio            # drizzle-kit studio — browser GUI for the database
pnpm db:seed              # tsx scripts/seed.ts — seed dev data
```

**Before every commit:** `pnpm typecheck && pnpm lint && pnpm test`

## Project Structure

```
.
├── app/                          # Next.js App Router (all routes live here)
│   ├── (marketing)/              # Route group: public pages (landing, pricing, blog)
│   │   ├── page.tsx              # Landing page (/)
│   │   ├── pricing/page.tsx
│   │   └── layout.tsx            # Marketing layout (header + footer, no sidebar)
│   ├── (auth)/                   # Route group: auth flows (no sidebar, centered)
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── forgot-password/page.tsx
│   │   └── layout.tsx            # Auth layout (centered card)
│   ├── (dashboard)/              # Route group: authenticated app
│   │   ├── dashboard/page.tsx    # Main dashboard
│   │   ├── settings/
│   │   │   ├── page.tsx          # Settings overview
│   │   │   └── billing/page.tsx  # Billing settings
│   │   ├── [teamId]/             # Dynamic: team-scoped routes
│   │   │   ├── page.tsx
│   │   │   └── members/page.tsx
│   │   └── layout.tsx            # Dashboard layout (sidebar + topbar)
│   ├── api/                      # API routes (external webhooks only — see rule below)
│   │   └── webhooks/
│   │       └── stripe/route.ts   # Stripe webhook handler
│   ├── layout.tsx                # Root layout (html, body, providers)
│   ├── not-found.tsx             # Global 404
│   ├── error.tsx                 # Global error boundary (client component)
│   └── loading.tsx               # Global loading (streaming fallback)
├── lib/                          # Shared library code (non-React)
│   ├── db/
│   │   ├── index.ts              # Database singleton + query helpers
│   │   ├── schema.ts             # Drizzle schema definitions (single file until >500 lines)
│   │   ├── migrations/           # Generated SQL migrations (never hand-edit)
│   │   └── seed.ts               # Dev seed data
│   ├── auth/
│   │   ├── index.ts              # Lucia auth setup + session helpers
│   │   ├── password.ts           # Argon2id hashing (via @node-rs/argon2)
│   │   └── middleware.ts         # Auth middleware for route protection
│   ├── email/
│   │   └── index.ts              # Email sending (Resend or SMTP)
│   ├── stripe/
│   │   ├── client.ts             # Stripe SDK singleton
│   │   ├── webhooks.ts           # Webhook event handlers
│   │   └── plans.ts              # Plan definitions + helpers
│   ├── validators/               # Zod schemas shared between client and server
│   │   ├── auth.ts               # Login, register, reset-password schemas
│   │   └── team.ts               # Team CRUD schemas
│   ├── env.ts                    # Environment variable validation (Zod, fails at build)
│   ├── constants.ts              # App-wide constants (plan limits, roles, etc.)
│   └── utils.ts                  # Pure utility functions (<200 lines or split)
├── components/
│   ├── ui/                       # Primitive UI components (shadcn/ui or hand-rolled)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── forms/                    # Form components (always client components)
│   │   ├── login-form.tsx
│   │   ├── register-form.tsx
│   │   └── team-settings-form.tsx
│   └── layouts/                  # Layout sub-components
│       ├── sidebar.tsx
│       ├── topbar.tsx
│       └── footer.tsx
├── actions/                      # Server Actions (the primary mutation layer)
│   ├── auth.ts                   # login, register, logout, resetPassword
│   ├── team.ts                   # createTeam, updateTeam, inviteMember
│   └── billing.ts               # createCheckout, manageBilling
├── hooks/                        # Client-side React hooks
│   ├── use-media-query.ts
│   └── use-debounce.ts
├── types/                        # TypeScript type definitions
│   └── index.ts                  # Shared types (keep thin — prefer Drizzle inference)
├── public/                       # Static assets
├── scripts/                      # CLI scripts (seed, migrate, one-off tasks)
│   └── seed.ts
├── tests/                        # Test files mirror source structure
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── data/                         # SQLite database directory
│   ├── app.db                    # Main database (git-ignored)
│   └── .gitkeep
├── .env.local                    # Local environment variables (git-ignored)
├── .env.example                  # Template with all required vars (committed)
├── drizzle.config.ts             # Drizzle Kit configuration
├── next.config.ts                # Next.js configuration
├── tsconfig.json
├── vitest.config.ts
├── playwright.config.ts
└── CLAUDE.md                     # This file
```

### File Organization Rules

1. **One export per file for components.** A file named `button.tsx` exports `Button`.
2. **Co-locate related code.** Route-specific components go in the route directory, not `/components`.
3. **200-400 lines per file.** If a file exceeds 500 lines, split it. No exceptions.
4. **No barrel files** (`index.ts` that re-exports). They break tree-shaking and create circular deps.
5. **Flat over nested.** `lib/validators/auth.ts` not `lib/validators/auth/schema/index.ts`.

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files (components) | `kebab-case.tsx` | `login-form.tsx` |
| Files (lib/utils) | `kebab-case.ts` | `password.ts` |
| React components | `PascalCase` | `LoginForm` |
| Functions | `camelCase` | `createTeam` |
| Server Actions | `camelCase`, verb-first | `updateTeamName`, `deleteInvite` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_TEAM_MEMBERS` |
| DB tables | `snake_case`, plural | `team_members` |
| DB columns | `snake_case` | `created_at` |
| DB foreign keys | `{referenced_table_singular}_id` | `team_id` |
| DB indexes | `idx_{table}_{column}` | `idx_users_email` |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` |
| CSS classes | Tailwind utilities only | No custom CSS files |
| Route groups | `(kebab-case)` | `(dashboard)` |
| Dynamic routes | `[camelCase]` | `[teamId]` |
| Test files | `*.test.ts` / `*.test.tsx` | `auth.test.ts` |

## Database Conventions

### SQLite-Specific Rules

1. **Use INTEGER PRIMARY KEY.** Not UUIDs. SQLite aliases INTEGER PRIMARY KEY to rowid — it is the fastest possible key. UUIDs destroy insert performance and waste space.
2. **Use Unix timestamps (INTEGER).** Not DATETIME strings. `Math.floor(Date.now() / 1000)` stores as 4 bytes, sorts correctly, and avoids timezone confusion. Drizzle's `integer('created_at', { mode: 'timestamp' })` handles conversion.
3. **Use TEXT for IDs shown to users.** Generate with `crypto.randomBytes(16).toString('base64url')` for public-facing IDs (URLs, API keys). Keep the internal INTEGER PRIMARY KEY for joins.
4. **Enable WAL mode at connection time.** `PRAGMA journal_mode=WAL` — mandatory for concurrent reads during writes.
5. **Enable foreign keys at connection time.** `PRAGMA foreign_keys=ON` — SQLite disables them by default.
6. **Use strict tables.** `STRICT` keyword on CREATE TABLE catches type errors.

### Schema Template (Drizzle)

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  publicId: text('public_id').notNull().unique(),      // URL-safe, shown to users
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  role: text('role', { enum: ['user', 'admin'] }).notNull().default('user'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
}, (table) => [
  index('idx_users_email').on(table.email),
  index('idx_users_public_id').on(table.publicId),
]);
```

### Migration Rules

1. **Never hand-edit generated migration SQL.** If a migration is wrong, delete it and regenerate.
2. **Never modify a migration that has been applied to production.** Create a new migration instead.
3. **Every migration must be reversible in theory.** Add comments documenting how to reverse destructive changes (column drops, table drops).
4. **Test migrations on a copy of production data** before deploying.
5. **Migration naming:** Drizzle auto-generates names. Do not rename the files.
6. **Seed data is not a migration.** Seeds go in `scripts/seed.ts` and are dev-only.

### Query Rules

```typescript
// CORRECT: parameterized query (safe)
db.select().from(users).where(eq(users.email, userInput));

// WRONG: string interpolation (SQL injection)
db.run(`SELECT * FROM users WHERE email = '${userInput}'`);
```

1. **Always use Drizzle query builder or parameterized statements.** Never interpolate user input into SQL.
2. **Wrap multi-step mutations in transactions.**
   ```typescript
   db.transaction((tx) => {
     tx.insert(teams).values({ name: teamName });
     tx.insert(teamMembers).values({ teamId: newTeamId, userId, role: 'owner' });
   });
   ```
3. **Select only needed columns.** `db.select({ id: users.id, email: users.email })` not `db.select()`.
4. **Add indexes for every column used in WHERE or JOIN.** Check with `EXPLAIN QUERY PLAN`.

## Server Component Patterns

### Data Fetching (Server Components Only)

```typescript
// app/(dashboard)/dashboard/page.tsx
import { db } from '@/lib/db';
import { projects } from '@/lib/db/schema';
import { requireAuth } from '@/lib/auth';
import { eq } from 'drizzle-orm';

export default async function DashboardPage() {
  const session = await requireAuth(); // Throws redirect if not authenticated

  const userProjects = await db
    .select({ id: projects.id, name: projects.name, updatedAt: projects.updatedAt })
    .from(projects)
    .where(eq(projects.userId, session.userId))
    .orderBy(desc(projects.updatedAt));

  return <ProjectList projects={userProjects} />;
}
```

**Rules:**
- Data fetching happens in Server Components (pages, layouts). Never in Client Components.
- No `useEffect` + `fetch` for data loading. That pattern creates waterfalls and breaks SSR.
- No API routes for internal data fetching. Call the database directly in Server Components.
- API routes exist only for external consumers: webhooks, mobile apps, third-party integrations.

### Client Components (Interactivity Only)

```typescript
'use client';
// components/forms/create-project-form.tsx
import { useActionState } from 'react';
import { createProject } from '@/actions/project';

export function CreateProjectForm() {
  const [state, action, isPending] = useActionState(createProject, null);

  return (
    <form action={action}>
      <input name="name" required minLength={1} maxLength={255} />
      {state?.error && <p className="text-red-600 text-sm">{state.error}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create Project'}
      </button>
    </form>
  );
}
```

**Rules:**
- Add `'use client'` only when the component needs interactivity (forms, event handlers, hooks).
- Keep Client Components as small as possible. Push data fetching and logic into Server Components.
- Never import server-only modules (db, auth internals) in Client Components.

## Server Actions Pattern

Server Actions are the primary mutation layer. Not API routes.

```typescript
// actions/project.ts
'use server';
import { db } from '@/lib/db';
import { projects } from '@/lib/db/schema';
import { requireAuth } from '@/lib/auth';
import { createProjectSchema } from '@/lib/validators/project';
import { revalidatePath } from 'next/cache';

type ActionState = { error?: string; success?: boolean } | null;

export async function createProject(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const session = await requireAuth();

  const parsed = createProjectSchema.safeParse({
    name: formData.get('name'),
  });

  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  try {
    db.insert(projects).values({
      name: parsed.data.name,
      userId: session.userId,
      publicId: generatePublicId(),
    }).run();

    revalidatePath('/dashboard');
    return { success: true };
  } catch (err) {
    console.error('[createProject]', err);
    return { error: 'Failed to create project. Please try again.' };
  }
}
```

**Rules:**
1. Every Server Action file starts with `'use server'`.
2. Every Action validates input with Zod before touching the database.
3. Every Action checks authentication before processing.
4. Actions return `{ error: string }` or `{ success: true }` — never throw to the client.
5. Actions call `revalidatePath()` or `revalidateTag()` after mutations.
6. Error messages shown to users are generic. Detailed errors go to `console.error` with a tag.

## Validation Pattern

Zod schemas are shared between client and server.

```typescript
// lib/validators/auth.ts
import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export const registerSchema = loginSchema.extend({
  name: z.string().min(1, 'Name is required').max(100),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
```

**Rules:**
- One validator file per domain (`auth.ts`, `team.ts`, `project.ts`).
- Export both the schema and the inferred TypeScript type.
- Client-side: use the schema for form validation hints.
- Server-side: use `.safeParse()` — never `.parse()` (it throws).

## Environment Variables

```bash
# .env.example — committed to git, no real values
DATABASE_URL="file:./data/app.db"
AUTH_SECRET="generate-with-openssl-rand-base64-32"

# Optional: Stripe billing
STRIPE_SECRET_KEY=""
STRIPE_WEBHOOK_SECRET=""
STRIPE_PRO_PRICE_ID=""

# Optional: Email
RESEND_API_KEY=""
EMAIL_FROM="noreply@example.com"
```

**Validate at build time:**

```typescript
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
  STRIPE_PRO_PRICE_ID: z.string().optional(),
  RESEND_API_KEY: z.string().optional(),
  EMAIL_FROM: z.string().email().optional(),
});

export const env = envSchema.parse(process.env);
```

**Rules:**
- Never access `process.env` directly except in `lib/env.ts`. Import `env` everywhere else.
- Never prefix secrets with `NEXT_PUBLIC_` — that exposes them in client bundles.
- `.env.local` is git-ignored. `.env.example` is committed.

## Error Handling Pattern

### Route-Level Error Boundaries

```
app/
├── error.tsx          # Global catch-all error boundary
├── not-found.tsx      # Global 404
├── (dashboard)/
│   ├── error.tsx      # Dashboard-specific error UI
│   └── loading.tsx    # Dashboard loading skeleton
```

**Rules:**
- Every route group gets its own `error.tsx` with context-appropriate UI.
- `error.tsx` must be a Client Component (`'use client'`).
- Always include a "Try Again" button that calls `reset()`.
- `loading.tsx` provides instant feedback — use skeleton UI, not spinners.
- Never show raw error messages to users. Log them server-side, show generic messages client-side.

## Auth Pattern

Using Lucia for session-based auth (no JWTs — JWTs cannot be revoked and add complexity).

```typescript
// lib/auth/index.ts — session validation helper
import { cookies } from 'next/headers';

export async function requireAuth() {
  const sessionId = (await cookies()).get('session')?.value;
  if (!sessionId) redirect('/login');

  const { session, user } = await lucia.validateSession(sessionId);
  if (!session) redirect('/login');

  return { session, user, userId: user.id };
}
```

**Rules:**
1. `requireAuth()` is called in every Server Component and Server Action that needs auth.
2. Passwords are hashed with Argon2id (`@node-rs/argon2`), not bcrypt (Argon2 is memory-hard, resists GPU attacks).
3. Sessions are stored in SQLite in a `sessions` table with an expiry column.
4. Middleware (`middleware.ts`) handles route protection at the edge — redirect unauthenticated users before the page renders.
5. Never expose user IDs in URLs. Use `publicId` (the `text` column from the schema above).

## Testing Strategy

### Test Structure

```
tests/
├── unit/                    # Pure functions, validators, utils
│   ├── validators/
│   │   └── auth.test.ts     # Zod schema validation tests
│   └── utils.test.ts
├── integration/             # Database operations, Server Actions
│   ├── actions/
│   │   └── auth.test.ts     # Login/register action tests
│   └── db/
│       └── users.test.ts    # Query helper tests
└── e2e/                     # Full user flows (Playwright)
    ├── auth.spec.ts         # Login → dashboard → logout
    └── billing.spec.ts      # Upgrade → manage → cancel
```

### Test Rules

1. **Target 80% coverage minimum.** Non-negotiable.
2. **Unit tests** for validators, utils, and pure functions. Fast, no I/O.
3. **Integration tests** for Server Actions and database queries. Use an in-memory SQLite database (`:memory:`).
4. **E2E tests** for critical flows: auth, billing, core CRUD.
5. **No snapshot tests.** They are brittle and provide false confidence.
6. **No mocking the database.** Use a real SQLite in-memory DB for integration tests.
7. **Test file naming:** `*.test.ts` for unit/integration, `*.spec.ts` for E2E.

### TDD Workflow

When adding features or fixing bugs:
1. **RED:** Write a failing test that describes the expected behavior.
2. **GREEN:** Write the minimum code to make it pass.
3. **REFACTOR:** Clean up without changing behavior. Tests must still pass.

## Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| LCP | < 1.5s | Lighthouse, `next build` report |
| FID | < 100ms | Lighthouse |
| CLS | < 0.1 | Lighthouse |
| DB query (p95) | < 50ms | Custom logging in `lib/db/index.ts` |
| Server Action (p95) | < 200ms | Custom logging in action wrapper |
| Build time | < 60s | CI pipeline |

## Security Checklist

Before every PR:
- [ ] No secrets in client bundles (check `NEXT_PUBLIC_` usage)
- [ ] All user input validated with Zod before database operations
- [ ] SQL queries use parameterized statements (Drizzle handles this)
- [ ] Passwords hashed with Argon2id, never stored as plaintext
- [ ] Sessions have expiry and can be revoked
- [ ] Webhook endpoints verify signatures (Stripe-Signature header)
- [ ] Rate limiting on auth endpoints (login, register, password reset)
- [ ] Error messages do not leak internal details (stack traces, SQL errors)
- [ ] CSRF protection via SameSite cookies (Lucia handles this)
- [ ] No `eval()`, `new Function()`, or `dangerouslySetInnerHTML`

## What We Do NOT Do (and Why)

| Anti-Pattern | Why Not | Do Instead |
|-------------|---------|------------|
| `useEffect` for data fetching | Creates waterfalls, breaks SSR, causes loading flicker | Fetch in Server Components with `async/await` |
| API routes for internal data | Unnecessary HTTP round-trip when you can query directly | Direct DB calls in Server Components |
| Prisma ORM | 8MB+ engine binary, async-only API mismatches SQLite, complex migrations | Drizzle ORM (zero runtime, type-safe, SQLite-native) |
| UUID primary keys | 3x slower inserts, 2x storage, fragments B-tree indexes in SQLite | INTEGER PRIMARY KEY (aliased to rowid) |
| JWT for auth sessions | Cannot revoke, requires refresh token dance, complex for server-rendered apps | Session tokens in SQLite (Lucia) |
| bcrypt for passwords | CPU-only, vulnerable to GPU/ASIC attacks | Argon2id (memory-hard, recommended by OWASP) |
| `SELECT *` | Returns unnecessary data, breaks when schema changes | Explicit column selection in every query |
| Barrel files (`index.ts` re-exports) | Breaks tree-shaking, creates circular dependencies, slows builds | Direct imports from the source file |
| CSS Modules / Styled Components | Extra build step, poor DX with Server Components, larger bundle | Tailwind CSS utility classes |
| Global state for server data | Stale data, hydration mismatches, unnecessary complexity | Server Components fetch fresh data on every request |
| `any` type | Disables type checking, hides bugs | `unknown` with type guards, or proper typing |
| Custom error classes | Over-engineering for a SaaS app, adds abstraction layers | Return `{ error: string }` from Actions, log details server-side |
| ORM-level soft deletes | Complicates every query with `WHERE deleted_at IS NULL` | Hard delete + audit log table if needed |

## Claude Code Configuration

### Hooks (`.claude/hooks/`)

These hooks automate quality enforcement during development:

#### PreToolUse: Block Destructive Commands

```jsonc
// .claude/settings.json (project-level)
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-bash-guard.sh \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/pre-bash-guard.sh
# Blocks dangerous commands before execution.
INPUT="$1"
BLOCKED_PATTERNS=(
  "rm -rf /"
  "DROP TABLE"
  "DROP DATABASE"
  "git push --force"
  "git reset --hard"
  "chmod 777"
  "pkill"
  "> /dev/sda"
)
for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$INPUT" | grep -qi "$pattern"; then
    echo "BLOCKED: Command matches dangerous pattern: $pattern"
    echo '{"decision": "block", "reason": "Destructive command blocked by PreToolUse hook"}'
    exit 0
  fi
done
echo '{"decision": "allow"}'
```

#### PostToolUse: Auto-Format on Save

```jsonc
// Added to the same hooks config
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post-format.sh \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/post-format.sh
# Auto-format files after Claude edits them.
FILE=$(echo "$1" | jq -r '.file_path // empty')
if [ -n "$FILE" ] && [ -f "$FILE" ]; then
  case "$FILE" in
    *.ts|*.tsx|*.js|*.jsx)
      npx prettier --write "$FILE" 2>/dev/null
      ;;
    *.sql)
      # Format SQL if sql-formatter is installed
      npx sql-formatter --fix "$FILE" 2>/dev/null || true
      ;;
  esac
fi
```

#### Stop Hook: Pre-Commit Quality Gate

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/stop-quality-gate.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/stop-quality-gate.sh
# Runs quality checks when Claude finishes a task.
echo "Running quality gate..."
ERRORS=0

# Type check
if ! pnpm typecheck 2>/dev/null; then
  echo "FAIL: TypeScript errors detected"
  ERRORS=$((ERRORS + 1))
fi

# Lint
if ! pnpm lint 2>/dev/null; then
  echo "FAIL: Lint errors detected"
  ERRORS=$((ERRORS + 1))
fi

# Tests
if ! pnpm test --run 2>/dev/null; then
  echo "FAIL: Test failures detected"
  ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
  echo "Quality gate: $ERRORS check(s) failed. Review before committing."
else
  echo "Quality gate: All checks passed."
fi
```

### MCP Servers (`.claude/settings.json`)

```jsonc
{
  "mcpServers": {
    // Filesystem access scoped to project directory only
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-fs", "--root", "."],
      "trust": "project"
    },
    // SQLite database access for direct queries during development
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-sqlite", "--db", "./data/app.db"],
      "trust": "project"
    }
  }
}
```

### Permission Modes

Use **plan mode** for exploratory tasks (architecture decisions, investigation). Switch to **auto-accept** mode only for well-defined, scoped tasks (e.g., "add a name field to the users table") with these allowed tools:

```jsonc
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(pnpm *)",
      "Bash(npx drizzle-kit *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Edit",
      "Write"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force*)",
      "Bash(git reset --hard*)",
      "Bash(DROP *)"
    ]
  }
}
```

### Memory System (`.claude/memory/`)

For long-running projects, maintain a memory file that persists across sessions:

```markdown
<!-- .claude/memory/MEMORY.md -->
# Project Memory

## Decisions
- 2024-01-15: Chose Lucia over NextAuth — simpler session model, SQLite-native
- 2024-01-20: Chose Drizzle over Prisma — sync API matches better-sqlite3
- 2024-02-01: No API routes for internal data — Server Components query DB directly

## Active Tasks
- [ ] Implement team invitation flow (actions/team.ts)
- [ ] Add Stripe webhook handler for subscription changes

## Constraints
- SQLite WAL mode required — always set PRAGMA journal_mode=WAL on connection
- No UUIDs for primary keys — INTEGER only (see DB conventions above)
- Auth sessions stored in DB — no JWTs
```

This file is automatically read at session start and updated as decisions are made.

### Agent Orchestration

For complex tasks, use sub-agents with specific roles:

```
# Multi-agent task example: "Add billing feature"

Agent 1 (Planner):    Break down into schema → actions → UI → tests
Agent 2 (TDD):        Write failing tests for billing actions
Agent 3 (Implement):  Write code to pass the tests
Agent 4 (Review):     Security review of payment handling
Agent 5 (E2E):        Write Playwright test for upgrade flow
```

**Agent routing rules:**
- Schema changes → always start with migration + tests
- UI changes → always start with Server Component, add Client Component only if interactivity needed
- Security-sensitive code (auth, payments) → always run security review agent
- Database queries → always verify with `EXPLAIN QUERY PLAN`

## Common Tasks

### Add a New Database Table

1. Add schema in `lib/db/schema.ts`
2. Run `pnpm db:generate` to create migration
3. Run `pnpm db:migrate` to apply
4. Add seed data in `scripts/seed.ts`
5. Create Zod validators in `lib/validators/`
6. Create Server Actions in `actions/`
7. Write tests for the actions

### Add a New Page

1. Create `app/(group)/route-name/page.tsx` as a Server Component
2. Fetch data directly from DB using Drizzle
3. Extract interactive parts into Client Components in `components/`
4. Add `loading.tsx` for streaming support
5. Add `error.tsx` for error handling

### Add a New Server Action

1. Create or update file in `actions/`
2. Add Zod schema in `lib/validators/`
3. Write integration test in `tests/integration/actions/`
4. Implement the action: validate → auth check → DB operation → revalidate
5. Wire up to a form component

## Git Conventions

**Commit format:** `<type>: <description>`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

**Branch naming:** `feat/short-description`, `fix/short-description`

**Before every commit:**
```bash
pnpm typecheck && pnpm lint && pnpm test
```

**PR checklist:**
- [ ] All checks pass (typecheck, lint, test)
- [ ] New code has tests (unit + integration minimum)
- [ ] No `console.log` left in committed code
- [ ] Migration tested on copy of production data (if applicable)
- [ ] No secrets in code or environment variable names changed in `.env.example`

---

*This CLAUDE.md is designed to be dropped into any greenfield Next.js 15 + SQLite SaaS project. Claude Code should be able to implement features, fix bugs, and make architectural decisions by referencing this file alone — no clarifying questions needed.*
