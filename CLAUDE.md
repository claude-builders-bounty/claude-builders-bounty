# CLAUDE.md - Next.js 15 + SQLite SaaS Template

> Opinionated, production-ready conventions. Every rule has a reason. Paste this into a greenfield project and Claude Code will understand the context without asking clarifying questions.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js | 15 (App Router) | React Server Components, streaming, server actions |
| Language | TypeScript | 5.6+ | Strict mode, exactOptionalPropertyTypes |
| Database | SQLite | 3.45+ (better-sqlite3) | Zero-config, file-based, 100k+ writes/sec |
| ORM | Drizzle | 0.33+ | Type-safe, fast, no runtime overhead |
| Auth | Lucia | 3.2+ | Session-based, framework-agnostic, SQLite-native |
| Validation | Zod | 3.23+ | Schema-first, inferred types |
| Styling | Tailwind | 3.4+ | Utility-first, JIT, dark mode |
| Testing | Vitest | 2.1+ | Native ESM, fast, Vite-native |
| Linting | Biome | 1.9+ | Fast, unified linter+formatter |

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth route group
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx     # Auth layout (no sidebar)
│   ├── (dashboard)/       # Protected route group
│   │   ├── _components/   # Dashboard-specific components
│   │   ├── settings/
│   │   ├── billing/
│   │   └── layout.tsx     # Dashboard layout (with sidebar)
│   ├── api/               # Server actions & route handlers
│   │   ├── auth/
│   │   ├── webhooks/
│   │   └── actions/       # Server actions (mutations)
│   ├── globals.css
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # Shared UI components
│   ├── ui/               # Base components (Button, Input, Card, etc.)
│   ├── forms/            # Form-specific components
│   ├── data-display/     # Tables, Lists, Charts
│   └── feedback/         # Toast, Modal, Alert
├── db/                   # Database layer
│   ├── index.ts          # Drizzle instance (singleton)
│   ├── schema/           # Table definitions
│   │   ├── users.ts
│   │   ├── sessions.ts
│   │   ├── organizations.ts
│   │   └── subscriptions.ts
│   ├── migrations/       # Generated SQL migrations
│   └── queries/          # Reusable query functions
├── lib/                  # Core utilities
│   ├── auth.ts           # Lucia auth helpers
│   ├── validation.ts     # Zod schemas
│   ├── utils.ts          # Generic helpers (cn, formatDate, etc.)
│   └── constants.ts      # App-wide constants
├── hooks/                # Custom React hooks
│   ├── useAuth.ts
│   ├── useToast.ts
│   └── useDebounce.ts
├── types/                # Global TypeScript types
│   ├── globals.d.ts
│   └── next-auth.d.ts
└── middleware.ts         # Next.js middleware (auth, i18n, etc.)
```

---

## SQL / Migration Conventions

### Naming
- Tables: `snake_case`, plural (`users`, `organization_members`)
- Columns: `snake_case` (`created_at`, `updated_at`)
- Primary keys: `id` (TEXT, ULID) or `id` (INTEGER AUTOINCREMENT)
- Foreign keys: `{table}_id` (`user_id`, `organization_id`)
- Indexes: `idx_{table}_{column(s)}`
- Unique constraints: `uq_{table}_{column(s)}`

### Drizzle Schema Patterns

```typescript
// db/schema/users.ts
import { sqliteTable, text, integer, index, uniqueIndex } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(createId), // ULID
  email: text('email').notNull(),
  emailVerified: integer('email_verified', { mode: 'boolean' }).default(false),
  passwordHash: text('password_hash'), // null for OAuth users
  name: text('name'),
  avatarUrl: text('avatar_url'),
  createdAt: integer('created_at', { mode: 'timestamp' }).$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).$defaultFn(() => new Date())
    .$onUpdate(() => new Date()),
}, (table) => ({
  emailIdx: uniqueIndex('uq_users_email').on(table.email),
  createdIdx: index('idx_users_created_at').on(table.createdAt),
}));

// Always export types
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
```

### Migration Commands
```bash
# Generate migration
npm run db:generate

# Apply migrations (dev)
npm run db:push

# Apply migrations (prod)
npm run db:migrate

# Studio UI
npm run db:studio
```

---

## Component Patterns

### Server Components First
```tsx
// Default to Server Components
// Use 'use client' ONLY when needed (interactivity, hooks, browser APIs)

import { getUser } from '@/db/queries/users';

export default async function ProfilePage({ params }: { params: { id: string } }) {
  const user = await getUser(params.id); // Direct DB access - no API layer
  return <UserProfile user={user} />;
}
```

### Client Components - Minimal & Focused
```tsx
// src/components/ui/Button.tsx
'use client';

import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50';
    const variants = {
      primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
      secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
      destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
      outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
      ghost: 'hover:bg-accent hover:text-accent-foreground',
      link: 'text-primary underline-offset-4 hover:underline',
    };
    const sizes = {
      default: 'h-10 px-4 py-2',
      sm: 'h-9 rounded-md px-3',
      lg: 'h-11 rounded-md px-8',
      icon: 'h-10 w-10',
    };
    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
```

### Form Components - Server Actions + Zod
```tsx
// src/app/(dashboard)/settings/profile/actions.ts
'use server';

import { z } from 'zod';
import { getSession } from '@/lib/auth';
import { updateUser } from '@/db/queries/users';

const profileSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
});

export async function updateProfile(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const parsed = profileSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await updateUser(session.userId, parsed.data);
  return { success: true };
}
```

```tsx
// src/app/(dashboard)/settings/profile/ProfileForm.tsx
'use client';

import { useActionState } from 'react';
import { updateProfile } from './actions';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export function ProfileForm({ initialData }: { initialData: { name: string; email: string } }) {
  const [state, formAction] = useActionState(updateProfile, { error: null, success: false });

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">Name</label>
        <Input id="name" name="name" defaultValue={initialData.name} />
        {state.error?.name && <p className="text-sm text-destructive">{state.error.name[0]}</p>}
      </div>
      <div>
        <label htmlFor="email" className="block text-sm font-medium mb-1">Email</label>
        <Input id="email" name="email" type="email" defaultValue={initialData.email} />
        {state.error?.email && <p className="text-sm text-destructive">{state.error.email[0]}</p>}
      </div>
      <Button type="submit" disabled={state.success}>
        {state.success ? 'Saved!' : 'Save Changes'}
      </Button>
      {state.success && <p className="text-sm text-green-600">Profile updated</p>}
    </form>
  );
}
```

---

## DB Migration Rules

1. **Never edit generated migrations** — regenerate instead
2. **One migration per logical change** — not per file
3. **Include rollback logic** for destructive changes
4. **Test migrations locally** before committing
5. **Name migrations descriptively**: `add_user_avatar_url`, `create_organization_members_table`

---

## Dev Commands

```bash
# Development
npm run dev                 # Next.js dev server (Turbopack)
npm run db:studio           # Drizzle Studio UI
npm run db:push             # Push schema changes to local DB

# Quality
npm run lint                # Biome lint + format
npm run typecheck           # tsc --noEmit
npm run test                # Vitest (unit)
npm run test:e2e            # Playwright (e2e)

# Build & Deploy
npm run build               # Next.js production build
npm run db:migrate          # Apply migrations (production)
npm run start               # Production server
```

---

## What We Don't Do (and Why)

| Pattern | ❌ Avoid | ✅ Prefer | Reason |
|---------|----------|-----------|--------|
| API Routes for CRUD | `/api/users` GET/POST | Server Actions + direct DB | Less boilerplate, type-safe, RSC-friendly |
| Prisma | Prisma Client | Drizzle ORM | 10x faster, no runtime, better TypeScript |
| NextAuth.js | NextAuth v4/v5 | Lucia Auth | Simpler, SQLite-native, no edge-case bugs |
| Redux/Zustand | Global state stores | Server state + React Context | Server Components don't need client state |
| Class Components | `class X extends React.Component` | Functions + Hooks | Modern, smaller bundle, better TS |
| `any` types | `const x: any = ...` | `unknown` + narrowing | Type safety catches bugs at compile time |
| Barrel exports | `export * from './ui'` | Named imports | Tree-shaking, explicit dependencies |
| `useEffect` for data | `useEffect(() => fetch(...))` | Server Components + Suspense | No waterfalls, streaming, SEO-friendly |
| CSS-in-JS | styled-components, emotion | Tailwind + CSS variables | Zero runtime, smaller bundle, faster dev |
| Custom hooks for everything | `useFetchUser()` | Direct async in Server Components | Less abstraction, clearer data flow |

---

## Anti-Patterns to Avoid

1. **Don't create API routes for internal data fetching** — use Server Components with direct DB access
2. **Don't put business logic in components** — extract to `lib/` or `db/queries/`
3. **Don't use `use client` on layout/page components** — only on interactive leaf components
4. **Don't skip Zod validation** — every external input must be validated
5. **Don't hardcode environment values** — use `lib/constants.ts` with `process.env`
6. **Don't commit `node_modules` or `.next`** — `.gitignore` handles this
7. **Don't use `console.log` in production code** — use structured logging (`lib/logger.ts`)

---

## Testing Strategy

| Layer | Tool | Coverage Target |
|-------|------|-----------------|
| Unit (utils, validators) | Vitest | 90%+ |
| Integration (queries, actions) | Vitest + Test DB | 80%+ |
| E2E (critical flows) | Playwright | 10 core flows |
| Visual (UI components) | Playwright + pixelmatch | Key components |

---

## Quick Start (3 Commands)

```bash
# 1. Clone & install
git clone <your-repo> && cd <your-repo> && npm install

# 2. Setup database
cp .env.example .env
npm run db:push

# 3. Develop
npm run dev
```

---

## Environment Variables (`.env.example`)

```env
# Database
DATABASE_URL="file:./dev.db"
# Or Turso: DATABASE_URL="libsql://your-db.turso.io?authToken=xxx"

# Auth
AUTH_SECRET="generate-with-openssl-rand-base64-32"
GITHUB_CLIENT_ID=""
GITHUB_CLIENT_SECRET=""
GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
NEXT_PUBLIC_APP_NAME="MySaaS"

# Optional
SENTRY_DSN=""
POSTHOG_KEY=""
```

---

*This CLAUDE.md is opinionated by design. Modify for your project, but understand the reasoning before changing conventions.*