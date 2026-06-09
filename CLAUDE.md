# Project: Next.js 15 + SQLite SaaS Starter

## Stack & Versions
- **Runtime:** Node.js 22 LTS
- **Framework:** Next.js 15 App Router (React 19)
- **Database:** better-sqlite3 (local dev) / Turso (production)
- **ORM:** Drizzle ORM
- **Auth:** NextAuth v5 (Auth.js) with credentials + OAuth
- **Styling:** Tailwind CSS v4
- **Validation:** Zod
- **Payments:** Stripe
- **Email:** Resend
- **Testing:** Vitest + Playwright

## Folder Structure
```
src/
├── app/           # Next.js App Router pages & API routes
│   ├── (auth)/    # Auth pages (login, register)
│   ├── (dashboard)/ # Protected dashboard pages
│   └── api/       # Route handlers
├── components/    # Shared React components
│   ├── ui/        # shadcn/ui primitives
│   └── forms/     # Form components with Zod validation
├── db/
│   ├── schema.ts  # Drizzle schema definitions
│   ├── migrations/ # SQL migration files (auto-generated)
│   └── seed.ts    # Development seed data
├── lib/
│   ├── auth.ts    # NextAuth configuration
│   ├── db.ts      # Database client singleton
│   └── utils.ts   # Shared utility functions
├── actions/       # Server Actions (form handlers, mutations)
├── hooks/         # Client-side React hooks
└── types/         # TypeScript type definitions
```

## Dev Commands
```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run db:generate  # Generate Drizzle migrations from schema changes
npm run db:migrate   # Apply pending migrations
npm run db:studio    # Open Drizzle Studio (DB visualizer)
npm run test         # Run Vitest unit tests
npm run test:e2e     # Run Playwright E2E tests
npm run lint         # ESLint + Prettier check
npm run format       # Auto-format with Prettier
```

## SQL / Migration Rules
1. **Any schema change requires a migration.** Never modify the DB directly.
2. Run `npm run db:generate` after editing schema.ts, then `npm run db:migrate`.
3. Migrations are committed to git. Never edit a migration after it's merged.
4. Use `text()` for timestamps with defaults: `created_at: text('created_at').default(sql\`CURRENT_TIMESTAMP\`)`.
5. Foreign keys are explicit: `.references(() => users.id, { onDelete: 'cascade' })`.
6. Index every column used in WHERE clauses. Add indexes as separate exports.
7. Dev uses better-sqlite3. Prod uses Turso. The client detects environment automatically.

## Component Patterns
### Server Components First
- Default to Server Components. Only add `'use client'` when you need interactivity.
- Fetch data directly in the component: `const data = await db.select().from(users)`.
- Pass data as props to client components.

### Form Handling
- Use Server Actions for form submission: `async function submit(formData: FormData) { 'use server'; ... }`.
- Validate with Zod before touching the database.
- Use `useActionState` for loading/error states in the form component.

### Data Access
- Never call the database from client components.
- Create Server Actions in `src/actions/` for mutations.
- For queries, fetch directly in server components.

## Naming Conventions
- **Files:** lowercase with hyphens: `user-profile.tsx`, `email-service.ts`
- **Components:** PascalCase, named export: `export function UserProfile() { ... }`
- **Database tables:** plural snake_case: `users`, `api_keys`, `billing_plans`
- **Columns:** snake_case: `user_id`, `created_at`, `stripe_customer_id`
- **Server Actions:** camelCase, prefixed with verb: `createUser`, `updateProfile`
- **TypeScript types:** PascalCase for types, no I-prefix for interfaces

## What We Don't Do (And Why)
1. **No API routes for data fetching.** Use Server Components or Server Actions instead. REST endpoints add indirection without benefit for internal data access.
2. **No ORM-level migrations.** Use Drizzle's SQL migration files. ORM-level sync works until it doesn't — explicit SQL is debuggable.
3. **No client-side data fetching with tRPC or React Query for internal data.** Server Components eliminate the need. Use tRPC/React Query only for real-time or external APIs.
4. **No environment variables on the client without NEXT_PUBLIC_ prefix.** Security. Server-only vars stay on the server.
5. **No raw SQL in components.** Put queries in Server Actions or db helper functions. Separation of concerns.
6. **No barrel exports (index.ts) for components.** They break tree-shaking and cause circular dependencies.
7. **No `any` type.** Use `unknown` and narrow with Zod if needed.
8. **No default exports for components.** Named exports enable better IDE support and refactoring.

## Testing Philosophy
- Unit tests for business logic in `lib/` and `actions/`.
- Component tests for shared UI components.
- E2E tests for critical user flows (signup → pay → access feature).
- Target: 80% coverage on business logic, 100% on payment/auth paths.
