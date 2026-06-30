# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Stack & Versions
- **Runtime**: Node.js 22 LTS
- **Framework**: Next.js 15 (App Router only — no `pages/`)
- **Language**: TypeScript 5.7+ (strict mode)
- **Database**: SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM**: Drizzle ORM — no raw SQL in application code
- **Styling**: Tailwind CSS v4 with `@tailwindcss/typography`
- **Auth**: NextAuth.js v5 (Auth.js) — email/password + OAuth providers
- **Validation**: Zod — validate at API boundary, trust inside
- **Payments**: Stripe (Checkout Sessions + Webhooks)
- **Email**: Resend (transactional) + React Email (templates)
- **Testing**: Vitest (unit) + Playwright (e2e)

## Folder Structure
```
src/
├── app/           # Next.js App Router (routes, layouts, loading, error)
│   ├── (auth)/    # Route group: login, register, forgot-password
│   ├── (dashboard)/ # Route group: authenticated pages
│   ├── api/       # Route handlers (NO pages/api/)
│   └── layout.tsx # Root layout (providers, fonts, metadata)
├── components/
│   ├── ui/        # shadcn/ui primitives (button, card, dialog, etc.)
│   └── features/  # Domain components (BillingForm, TeamSwitcher)
├── db/
│   ├── schema.ts  # Drizzle table definitions
│   ├── index.ts   # Database client initialization
│   └── migrations/ # Auto-generated migration files
├── lib/
│   ├── auth.ts    # NextAuth configuration
│   ├── stripe.ts  # Stripe client & helpers
│   └── utils.ts   # cn(), formatDate(), slugify() etc.
├── actions/       # Server Actions (useActionState, revalidatePath)
├── emails/        # React Email templates
└── validations/   # Zod schemas (shared between client & server)
```

## Naming Conventions
- **Files**: kebab-case (`user-profile.tsx`, `billing-form.tsx`)
- **Components**: PascalCase (`UserProfile`, `BillingForm`)  
- **Functions**: camelCase (`getUserById`, `createCheckoutSession`)
- **DB Tables**: snake_case plural (`users`, `team_members`, `subscriptions`)
- **DB Columns**: snake_case (`created_at`, `stripe_customer_id`)
- **Route Params**: camelCase (`[teamId]`, `[invoiceId]`)
- **Zod schemas**: PascalCase matching domain (`CreateTeamSchema`, `UpdateProfileSchema`)

## Dev Commands
```bash
pnpm dev          # Start dev server (Turbopack)
pnpm build        # Production build
pnpm lint         # ESLint + Prettier
pnpm test         # Vitest unit tests
pnpm test:e2e     # Playwright e2e tests
pnpm db:generate  # Generate Drizzle migrations
pnpm db:migrate   # Apply migrations
pnpm db:studio    # Open Drizzle Studio
pnpm stripe:listen # Stripe webhook forwarding
```

## Database Conventions
- **Migrations**: Always generated via `drizzle-kit generate` — NEVER hand-write SQL
- **Soft deletes**: Use `deleted_at TIMESTAMP` column, filter with `.where(isNull(table.deleted_at))`
- **Timestamps**: Every table gets `created_at` and `updated_at` (auto-set via Drizzle `defaultNow()`)
- **IDs**: Use `text('id').primaryKey().$defaultFn(() => crypto.randomUUID())` — never auto-increment
- **Foreign keys**: Always define `references()` with `onDelete` behavior explicit
- **No Views/Triggers**: Keep logic in application layer

## Component Patterns
- **Server Components first**: Default to `'use server'` mark. Add `'use client'` ONLY when you need `useState`, `useEffect`, `onClick`, or browser APIs.
- **Data fetching**: Server Components fetch directly in the component body. Client components use SWR for client-side fetching.
- **Form handling**: Use Server Actions (`action={myAction}`) with `useActionState` for state. Validate with Zod in the action, return `{ error, data }`.
- **Loading states**: Every async route gets a `loading.tsx` skeleton. Use `<Suspense>` for granular loading.
- **Error boundaries**: Every route gets `error.tsx`. Server actions catch errors and return them — never throw across server/client boundary.

## Anti-Patterns (What We Don't Do)
- ❌ **No API routes for mutations**: Use Server Actions instead. API routes are for webhooks only.
- ❌ **No client-side data fetching in layout**: Layouts can't use SWR. Fetch in page or use Server Component.
- ❌ **No ORM in client components**: Drizzle runs server-side only. Pass data as props.
- ❌ **No env vars in client code without `NEXT_PUBLIC_`**: Vite-style `import.meta.env` is NOT available.
- ❌ **No `any` types**: If you truly can't type it, use `unknown` with a type guard.
- ❌ **No barrel exports from `components/ui/`**: shadcn/ui components are imported individually.
- ❌ **No raw `<a>` for internal links**: Always use `<Link>` from `next/link`.
- ❌ **No `fetch` in Server Actions without revalidation**: Always call `revalidatePath()` after mutations.

## Environment Variables
```env
# Required
DATABASE_URL="file:./data.db"          # SQLite for dev, Turso URL for prod
AUTH_SECRET="openssl rand -base64 32"  # NextAuth encryption key
STRIPE_SECRET_KEY="sk_..."             # Stripe secret
STRIPE_WEBHOOK_SECRET="whsec_..."      # Stripe webhook signing secret
RESEND_API_KEY="re_..."                # Resend for transactional email

# Optional
NEXT_PUBLIC_APP_URL="http://localhost:3000"
STRIPE_PRICE_PRO_BASIC="price_..."     # Product price IDs
```

## Testing Philosophy
- **Unit tests**: Test pure functions, Zod schemas, and utility helpers. File alongside: `utils.test.ts`.
- **Integration tests**: Test Server Actions by calling them directly with mocked DB.
- **E2E tests**: Test critical user flows only (signup → create team → invite → pay). Use Playwright with `setup` project for auth state.
- **Don't test**: UI layout details, shadcn/ui components (already tested upstream), exact CSS classes.