# CLAUDE.md

This file defines how Claude Code should work in this repository.
It is intentionally opinionated for a production-minded Next.js 15 + SQLite SaaS.

## 1) Stack and Runtime Baseline

- Rule: Use Node.js 22 LTS and `pnpm` for all package management.
- Why: Mixed runtimes/package managers create lockfile drift and non-reproducible CI.

- Rule: Use Next.js 15 App Router with TypeScript `strict: true`.
- Why: App Router + strict typing catches architecture and data-shape bugs early.

- Rule: Use Drizzle ORM and Drizzle Kit for schema and migrations.
- Why: SQL stays explicit while schema changes remain versioned and reviewable.

- Rule: Use SQLite locally (`better-sqlite3`) and optionally Turso in hosted environments.
- Why: Local-first development remains fast while keeping a clear upgrade path for production.

## 2) Canonical Project Layout

```text
.
├── app/
│   ├── (marketing)/
│   ├── (app)/
│   │   ├── dashboard/
│   │   └── settings/
│   ├── api/
│   ├── _components/
│   └── _lib/
├── db/
│   ├── schema/
│   ├── migrations/
│   ├── seeds/
│   └── client.ts
├── src/
│   ├── features/
│   ├── server/
│   ├── lib/
│   └── types/
├── scripts/
├── public/
└── tests/
```

- Rule: Route files live under `app/`; business logic stays in `src/` and `db/`.
- Why: Routing concerns and domain logic stay separate, reducing accidental coupling.

- Rule: Put route-specific UI helpers in `app/**/_components` and reusable UI in `src/features/*/components`.
- Why: Avoids dumping everything into a global component bucket.

- Rule: Keep all database artifacts in `db/` (`schema`, `migrations`, `seeds`, client wiring).
- Why: DB review and operational ownership become straightforward.

## 3) Naming and File Conventions

- Rule: React components are `PascalCase.tsx`; hooks are `useXxx.ts`; utilities are `camelCase.ts`.
- Why: File names signal intent instantly and reduce cognitive overhead in reviews.

- Rule: Use feature folders (`src/features/billing`, `src/features/auth`) rather than type folders.
- Why: Feature ownership scales better than global `components/utils/services` sprawl.

- Rule: Server-only code must live in `src/server/**` and include `import 'server-only'` where appropriate.
- Why: Prevents secret-bearing logic from leaking into client bundles.

## 4) Database and Migration Rules

- Rule: Never edit an already-committed migration; create a new migration for every schema change.
- Why: Immutable migration history is required for deterministic deploys.

- Rule: One logical schema change per migration PR.
- Why: Smaller migrations are easier to review, roll back, and bisect.

- Rule: Generate migrations with Drizzle Kit, then manually review SQL before applying.
- Why: Generated SQL can be syntactically valid but operationally risky.

- Rule: Include index and constraint decisions in the migration itself (not deferred TODOs).
- Why: Data integrity and query performance should not depend on future cleanup.

- Rule: For destructive changes (drop/rename), ship a two-step plan (expand -> migrate data -> contract).
- Why: Direct destructive DDL causes outages and difficult recovery.

- Rule: For Turso targets, verify WAL-friendly workflows and avoid long write transactions.
- Why: SQLite-family databases are sensitive to write lock duration.

## 5) Component and Rendering Patterns

- Rule: Default to Server Components; opt into Client Components only when interactivity requires it.
- Why: Reduces client bundle size and improves TTFB.

- Rule: Data fetching belongs in server boundaries (`page.tsx`, server actions, or server utilities).
- Why: Keeps secrets and DB access off the client.

- Rule: Use Zod validation at all external boundaries (forms, webhooks, API handlers).
- Why: Runtime validation closes gaps TypeScript cannot enforce at runtime.

- Rule: Mutations must return typed result objects (`{ ok: boolean, error?: string }`) instead of throwing for expected failures.
- Why: Predictable failure shapes simplify UI handling and telemetry.

## 6) Dev Commands and Workflow

Use `pnpm` commands exactly:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

- Rule: Run `lint`, `typecheck`, and relevant tests before every PR.
- Why: Review should focus on design and correctness, not avoidable breakage.

- Rule: Every DB-affecting PR must run `pnpm db:generate` and include the migration diff.
- Why: Schema changes without migration artifacts are not deployable.

## 7) Security and Secrets

- Rule: Never commit `.env*` files or tokens; use local env files and CI secrets only.
- Why: Secret leaks are irreversible once pushed.

- Rule: Redact tokens, cookies, and user PII from logs, screenshots, and test fixtures.
- Why: Debug artifacts often outlive their original access controls.

## 8) What We Do Not Do (And Why)

- Rule: Do not use Prisma in this project.
- Why: We standardize on Drizzle to keep migration and query patterns consistent.

- Rule: Do not put SQL strings inside React components.
- Why: View code must stay presentation-focused and testable.

- Rule: Do not call external APIs directly from client components when secrets are required.
- Why: Client bundles are inspectable and cannot safely store credentials.

- Rule: Do not skip migration reviews just because SQL was generated.
- Why: Tool-generated SQL still needs human judgment for data safety.

- Rule: Do not add shared global state for one-off local component concerns.
- Why: Over-centralized state increases incidental complexity and rerender churn.

## 9) Claude Code Execution Style for This Repo

- Rule: When editing, propose the smallest coherent change that satisfies acceptance criteria.
- Why: Small, scoped patches reduce regression risk.

- Rule: If requirements are ambiguous, make one concrete assumption and document it in the PR notes.
- Why: Progress beats deadlock, and assumptions stay reviewable.

- Rule: When touching DB schema, include migration + code + test updates in one PR.
- Why: Partial schema work creates broken intermediate states.

- Rule: Prefer deterministic scripts/checks over manual one-off commands.
- Why: Repeatable workflows improve CI reliability and onboarding.
