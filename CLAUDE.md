# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions
- **Runtime**: Node.js 22 LTS
- **Framework**: Next.js 15 App Router (React 19, RSC-first)
- **Language**: TypeScript 5.7+ (strict mode)
- **Database**: SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM**: Drizzle ORM (edge-compatible, lightweight)
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth
- **Styling**: Tailwind CSS v4
- **Validation**: Zod (shared between client and server)
- **Payments**: Stripe (server-side only)
- **Email**: Resend (React Email templates)
- **Testing**: Vitest + React Testing Library
- **Linting**: Biome (format + lint, replaces ESLint + Prettier)

## Folder Structure
```
src/
  app/                  # App Router pages & API routes
    (auth)/             # Auth route group (login, register)
    (dashboard)/        # Protected dashboard group
      layout.tsx        # Dashboard shell layout (sidebar, nav)
      settings/         # User settings
      billing/          # Stripe billing portal
    api/                # Route handlers (/api/*)
      webhooks/         # Stripe/Resend webhook receivers
  components/
    ui/                 # shadcn/ui primitives
    forms/              # Form components (react-hook-form + zod)
    layout/             # Sidebar, header, shell
    data-table/         # TanStack Table wrappers
  lib/
    db/                 # Drizzle schema, migrations, seed
    auth/               # NextAuth config, callbacks, adapters
    stripe/             # Stripe client init (server-only)
    email/              # Resend client + templates
    utils/              # cn(), formatCurrency(), etc.
  server/
    actions/            # Server Actions (use server)
    queries/            # Data access functions
  hooks/                # Client hooks (useAuth, useMediaQuery)
  types/                # Shared TypeScript types
drizzle/                # Drizzle migrations (auto-generated)
public/                 # Static assets
```

## SQL / Migration Conventions

### Schema File
- Single `src/lib/db/schema.ts` — one file, all tables
- Export tables as named exports: `export const users = sqliteTable(...)`
- Always define `createdAt` and `updatedAt` with defaults:
  ```ts
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`).notNull(),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`).notNull(),
  ```
- Use `text("id").primaryKey()` for UUIDs, never auto-increment ints
- Foreign keys: always ON DELETE CASCADE for child rows, RESTRICT for referenced parents
- Index every column used in WHERE clauses of frequent queries

### Migrations
- `pnpm db:generate` — creates migration SQL from schema changes
- `pnpm db:migrate` — applies migrations to local SQLite DB
- `pnpm db:push` — for prototyping only (skips migration files)
- Never manually edit migration files
- Commit ALL migration files — they are the source of truth
- Run `pnpm db:generate` after every schema change in a PR

### Query Patterns
- Server Components: import query functions directly from `src/server/queries/`
- Route Handlers / Server Actions: same pattern
- NEVER use Drizzle client directly in React components
- NEVER pass raw DB results to client components — serialize first
- Use `drizzle-zod` to generate Zod schemas from table definitions:
  ```ts
  import { createSelectSchema } from "drizzle-zod";
  export const userSchema = createSelectSchema(users);
  ```

## Component Patterns

### Server Components (default, no `"use client"`)
- Data fetching directly in the component (async)
- Pass serialized data to client children via props
- Example:
  ```tsx
  export default async function DashboardPage() {
    const user = await getCurrentUser();
    return <DashboardClient user={user} />;
  }
  ```

### Client Components (explicit `"use client"`)
- Interactive UI: forms, buttons, modals, toasts
- Use hooks freely
- Receive data via props, never fetch directly
- Form pattern:
  ```tsx
  "use client";
  import { useForm } from "react-hook-form";
  import { zodResolver } from "@hookform/resolvers/zod";
  ```

### Server Actions
- Defined in `src/server/actions/` with `"use server"` directive
- One file per domain: `auth.ts`, `billing.ts`, `settings.ts`
- Always validate input with Zod at the top:
  ```ts
  "use server";
  const schema = z.object({ name: z.string().min(2) });
  export async function updateProfile(input: z.infer<typeof schema>) {
    const parsed = schema.safeParse(input);
    if (!parsed.success) return { error: "Invalid input" };
    // ... mutation logic
  }
  ```
- Revalidate paths after mutation: `revalidatePath("/dashboard")`
- Return `{ error?: string; success?: boolean }` — never throw

## Dev Commands
```bash
pnpm dev              # Next.js dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm db:generate      # Generate Drizzle migrations
pnpm db:migrate       # Apply migrations
pnpm db:studio        # Drizzle Studio (localhost:4983)
pnpm db:seed          # Seed dev database
pnpm test             # Run Vitest
pnpm test:watch       # Vitest watch mode
pnpm lint             # Biome check
pnpm lint:fix         # Biome auto-fix
pnpm stripe:listen    # Stripe webhook forwarding
```

## Anti-Patterns — What We Don't Do (And Why)

| Avoid | Because |
|-------|---------|
| `useEffect` for data fetching | Server Components or React Query handle this |
| Raw SQL strings in components | Goes through Drizzle and query layer |
| `any` type | TypeScript strict mode — define the type |
| `// @ts-ignore` | Fix the types or add a proper type assertion |
| Mixing ORMs (Prisma + Drizzle) | Pick one. We picked Drizzle |
| `export default` for utilities | Named exports for treeshaking and IDE autocompletion |
| `.env` committed to git | Use `.env.example` with placeholder values |
| Client-side Stripe SDK | All Stripe calls go through server actions |
| Inline styles or `style={{}}` | Tailwind covers all styling needs |
| `fetch` without error handling | Always check `if (!res.ok)` and return meaningful errors |
| Hardcoded URLs | Use `process.env.NEXT_PUBLIC_APP_URL` |
| Nested ternary operators | Extract to named variables or `if` statements |
| Mutating props | Props are read-only. Lift state up or use callbacks |

## Auth Conventions
- Protected routes go in `(dashboard)` route group with a layout that checks session
- Public pages: marketing, login, register, API webhooks
- Session check in Server Components:
  ```ts
  const session = await auth();
  if (!session?.user) redirect("/login");
  ```
- User ID from session: `session.user.id` (always a UUID string)

## Commit Conventions
- `feat:` new features
- `fix:` bug fixes
- `refactor:` code restructuring (no behavior change)
- `chore:` deps, config, CI
- `docs:` documentation only
