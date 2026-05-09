# CLAUDE.md — Next.js 15 + SQLite SaaS Stack

## Stack & Versions
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **Database:** SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM:** Drizzle ORM
- **Auth:** NextAuth.js v5 (Auth.js)
- **Styling:** Tailwind CSS v4 + shadcn/ui
- **Validation:** Zod
- **Payments:** Stripe
- **Email:** Resend

## Folder Structure
```
src/
├── app/            # Next.js App Router (routes only, no logic)
│   ├── (auth)/     # Auth route group
│   ├── (dashboard)/# Authenticated route group
│   └── api/        # API routes
├── components/     # React components
│   ├── ui/         # shadcn/ui primitives
│   └── features/   # Domain-specific components
├── lib/            # Shared utilities
│   ├── db/         # Database (schema, migrations, queries)
│   ├── auth/       # Auth config
│   └── utils/      # Pure helpers
├── server/         # Server-only code (never imported in client components)
│   └── actions/    # Server Actions
└── types/          # Shared TypeScript types
```

## Rules

### Database
- **All schema changes via Drizzle migrations** — never edit SQLite files directly
- `npx drizzle-kit generate` → review generated SQL → `npx drizzle-kit push`
- Queries go in `src/lib/db/queries/`, one file per domain (e.g. `users.ts`, `billing.ts`)
- **Never use raw SQL** unless Drizzle cannot express it. If you must, wrap in a migration
- Turso in production uses HTTP API — all queries must be compatible (no `ATTACH`, no `PRAGMA` volatile)

### Components
- **Server Components by default** — only add `"use client"` when you need interactivity
- Client boundary at the leaf: a `PostsList` is server, the `LikeButton` inside it is client
- Forms use Server Actions: define in `src/server/actions/`, import in form `action` prop
- **No `useEffect` for data fetching** — use Server Components, `fetch()`, or React Query for client-side
- shadcn/ui components are installed via `npx shadcn-ui add`, never edited manually in `components/ui/`

### Types & Validation
- Zod schemas in `src/lib/validations/`, co-located with the domain they validate
- Database types from Drizzle schema: `type User = typeof users.$inferSelect`
- **Never use `any`** — if typing is complex, create an interface
- API routes validate input with Zod before any logic

### Naming
- **Files:** kebab-case (`user-settings.ts`, `billing-webhook.ts`)
- **Components:** PascalCase (`UserSettings.tsx`)
- **Functions:** camelCase (`getUserByEmail`, `createCheckoutSession`)
- **Database tables:** plural snake_case (`users`, `subscription_plans`)
- **Branches:** `feat/description`, `fix/description`, `chore/description`

## Dev Commands
```bash
pnpm dev           # Start dev server (localhost:3000)
pnpm build         # Production build
pnpm db:generate   # Generate Drizzle migrations
pnpm db:push       # Apply migrations
pnpm db:studio     # Open Drizzle Studio
pnpm lint          # ESLint
pnpm format        # Prettier
pnpm test          # Vitest
```

## Anti-Patterns (What We Don't Do)

### ❌ Don't
- Put business logic in components — it goes in `lib/` or `server/actions/`
- Import server code in client components — use Server Actions or API routes
- Store secrets in `.env` — use `.env.local` (gitignored), `.env.example` for templates
- Use `useEffect` for data fetching — React Query or Server Components
- Direct SQLite file manipulation — always through Drizzle
- Mix concerns in a single file — one file, one responsibility
- Skip Zod validation on user input — everything from the boundary gets validated

### ✅ Do
- **Server-first data fetching** — the data lives on the server, components receive it as props
- **Progressive enhancement** — form works without JS, enhanced with `useFormStatus`
- **Edge-compatible where possible** — avoid Node.js APIs in route handlers (use Web APIs)
- **Tailwind over CSS modules** — one styling system, no mixing
- **Co-locate tests** — `__tests__` directory next to the code it tests

## When in Doubt
1. Check the Next.js docs before implementing routing/auth patterns
2. Search existing `lib/db/queries/` for similar data access patterns
3. New domain? Start with the Zod schema, then the DB schema, then the UI
4. If a component is hard to test, it probably does too much — split it
