# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

This file defines the patterns, conventions, and anti-patterns for this project.
Claude Code reads this file on every session — keep it sharp.

## 🏗 Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript (strict mode)
- **Database**: better-sqlite3 via Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js)
- **CSS**: Tailwind CSS v4
- **Validation**: Zod
- **Testing**: Vitest + Playwright

## 📁 Folder Structure

```
src/
├── app/              # Next.js App Router pages
│   ├── (auth)/       # Auth group: login, register
│   ├── (dashboard)/  # Dashboard group: authenticated pages
│   ├── api/          # API route handlers
│   └── layout.tsx    # Root layout
├── components/       # Shared React components
│   ├── ui/           # Primitives (Button, Input, Card, etc.)
│   └── forms/        # Form components
├── db/               # Database
│   ├── schema/       # Drizzle schema files
│   ├── migrations/   # Auto-generated migrations
│   └── index.ts      # DB client singleton
├── lib/              # Utility functions & shared logic
│   ├── auth.ts       # Auth.js configuration
│   └── utils.ts      # General helpers
├── actions/          # Server Actions (one file per domain)
│   ├── auth.actions.ts
│   ├── project.actions.ts
│   └── billing.actions.ts
└── types/            # TypeScript type definitions
```

## ✅ DO

### Component Patterns

- **Server Components** by default. Client Components (`"use client"`) only when:
  - Using `useState`, `useEffect`, or browser APIs
  - Handling user interactions (onClick, onSubmit)
  - Using context providers
- **Composition over props drilling** — use `children` and slot patterns.
- **One component per file**, named after the file.
- Props interface exported: `export interface ButtonProps { ... }`

### Database Conventions

- All schema files go in `src/db/schema/`, one file per domain entity.
- Migrations are auto-generated via `drizzle-kit push` — never edit manually.
- Queries go in Server Components or Server Actions, never in Client Components.
- Use transactions for multi-table writes:
  ```ts
  await db.transaction(async (tx) => { ... })
  ```

### API Routes

- Every API route must validate input with Zod.
- Return consistent response shape:
  ```ts
  { success: true, data: ... } | { success: false, error: string }
  ```
- Rate-limit authenticated endpoints using headers or middleware.

### Server Actions

- Named `*.actions.ts` — co-located by domain, not by type.
- Always return serializable responses (no JSX, no Date objects without serialization).
- Handle errors gracefully — never throw uncaught errors.

### Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files | kebab-case | `user-profile.tsx` |
| Components | PascalCase | `UserProfile` |
| Functions | camelCase | `fetchUserData()` |
| Types/Interfaces | PascalCase | `UserProfileData` |
| DB tables | snake_case | `user_profiles` |
| DB columns | snake_case | `created_at` |
| Env vars | UPPER_SNAKE_CASE | `DATABASE_URL` |

### Git Conventions

- Branch naming: `feat/description`, `fix/description`, `chore/description`.
- Commits: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`).
- Squash merge feature branches — no merge commits.

## ❌ NEVER DO

- **`rm -rf` in any script** — use `trash` CLI or `fs.unlink` in Node.
- **`git push --force` on main branches** — use `--force-with-lease`.
- **Inline CSS** — use Tailwind classes or CSS modules.
- **Nested client components** — keep "use client" at leaf level.
- **Magic strings or numbers** — export constants.
- **`any` type** — prefer `unknown` with proper narrowing.
- **Hardcoded secrets** — use `process.env` with Zod validation on startup.
- **Mutate props directly** — treat props as read-only.
- **`useEffect` for data fetching** — use Server Components or React Query.
- **Direct DB access from Client Components** — use Server Actions.

## 🚀 Dev Commands

```bash
npm run dev        # Start dev server (localhost:3000)
npm run build      # Production build
npm run lint       # ESLint check
npm run test       # Vitest unit tests
npm run test:e2e   # Playwright E2E tests
npm run db:push    # Push schema to local DB
npm run db:studio  # Open Drizzle Studio
npm run db:seed    # Seed development data
npm run typecheck  # tsc --noEmit (strict check)
```

## 💡 Design Principles

1. **Fail fast** — validate at the boundary (Zod schema on API/S.A. entry).
2. **Progressive enhancement** — forms work without JS if possible.
3. **Explicit over implicit** — no magic imports, no barrel files for components.
4. **Ship small** — one feature per PR, one concern per file.
5. **Accessibility first** — semantic HTML, proper ARIA labels, keyboard navigation.

## 📦 Dependencies Policy

- Pin exact versions in `package.json` — no `^` or `~`.
- Audit dependencies weekly (`npm audit`).
- Evaluate bundle impact before adding new packages.
- Prefer native Web APIs over npm packages when feasible.
