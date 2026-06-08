# CLAUDE.md

Guidance for Claude Code when working in this Next.js + SQLite SaaS project.

## Project Shape

- App framework: Next.js App Router with TypeScript.
- Database: SQLite for local and small-team deployments.
- ORM: Prisma or Drizzle. Follow the ORM already present in the repository.
- Styling: Tailwind CSS plus local component primitives.
- Auth, billing, email, and background jobs should be treated as production-critical paths.

## Core Commands

Run the package manager already used by the project. Prefer `pnpm` if a `pnpm-lock.yaml` exists, `npm` if `package-lock.json` exists, and `yarn` if `yarn.lock` exists.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

If the project uses npm:

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test
npm run build
```

## Environment

Never invent or commit secrets. Use `.env.example` as the source of truth and keep `.env.local` private.

Common values:

```text
DATABASE_URL="file:./dev.db"
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
RESEND_API_KEY=
```

## SQLite Rules

- Treat SQLite writes as single-node and transactional.
- Avoid long-running write transactions.
- Add indexes for columns used in frequent filters, joins, or uniqueness checks.
- Use foreign keys where the ORM supports them.
- For destructive schema changes, preserve data with a migration plan and a rollback note.
- Do not delete or recreate the local database unless the user explicitly asks.

## ORM Rules

### Prisma

```bash
pnpm prisma generate
pnpm prisma migrate dev
pnpm prisma studio
```

- Edit `prisma/schema.prisma`, then generate and migrate.
- Do not hand-edit generated Prisma client files.
- Include migration files in commits.

### Drizzle

```bash
pnpm drizzle-kit generate
pnpm drizzle-kit migrate
pnpm drizzle-kit studio
```

- Keep schema definitions in the established `db/schema` location.
- Use explicit names for relations, indexes, and constraints when helpful.
- Include generated migration SQL in commits.

## Next.js Rules

- Prefer Server Components for data fetching and read-only views.
- Use Server Actions or route handlers for mutations.
- Keep client components small and only use `"use client"` when browser state, effects, or event handlers are needed.
- Validate all mutation inputs with the project's existing schema library, usually Zod.
- Use `revalidatePath`, `revalidateTag`, or router refresh intentionally after mutations.
- Avoid leaking server-only environment variables into client bundles.

## SaaS Domain Rules

- Billing changes need idempotency and webhook tests.
- Auth and invitation flows need authorization checks on the server.
- Organization, workspace, or tenant IDs must be scoped in every query.
- Soft-delete customer-owned records unless product requirements say otherwise.
- Audit logs are required for billing, role, and destructive data changes.

## Testing Expectations

- Add unit tests for pure utilities and validation schemas.
- Add integration tests for database queries and mutations.
- Add at least one regression test for every bug fix.
- For UI changes, include the important loading, empty, error, and success states.
- Run lint, typecheck, tests, and build before handing off.

## Code Style

- Use TypeScript strict types and avoid `any` unless the project already has a typed boundary.
- Prefer small functions with explicit input and output types.
- Keep database access in the project's existing data layer.
- Use existing UI components before creating new ones.
- Keep copy concise and product-facing.

## Safety

- Never run `rm -rf`, force-push, reset, or delete databases without explicit user approval.
- Before migrations, inspect the current schema and existing migrations.
- Before touching auth, billing, or tenant isolation, find the tests and add coverage.
- If a request conflicts with data safety, stop and ask for confirmation.

## PR Checklist

- [ ] `lint` passes
- [ ] `typecheck` passes
- [ ] tests pass
- [ ] build passes
- [ ] migrations included when schema changes
- [ ] `.env.example` updated for new environment variables
- [ ] no secrets committed
- [ ] screenshots or notes included for UI changes
