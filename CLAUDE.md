# CLAUDE.md

Instructions for Claude Code working on a greenfield Next.js 15 App Router SaaS with SQLite.

Use these rules as the project defaults. If the real repository already contradicts a rule, preserve the repository behavior and update this file in the same PR.

## Stack and versions

| Area | Default | Reason |
| --- | --- | --- |
| Runtime | Node.js 22 LTS, pnpm 10 | Stable native fetch, modern tooling, reproducible installs. |
| Framework | Next.js 15 App Router, React 19, TypeScript strict | Server Components and Server Actions are first-class; strict types catch data boundary mistakes early. |
| Styling | Tailwind CSS 4 with CSS variables | Fast UI iteration without scattering one-off styles. |
| Database | SQLite through Drizzle ORM | SQLite keeps dev/prod simple; Drizzle keeps SQL visible and migrations reviewable. |
| Local DB driver | `better-sqlite3` | Synchronous local adapter is simple and reliable for tests and scripts. |
| Hosted DB driver | Turso/libSQL via `@libsql/client` | Gives SQLite semantics with edge-friendly hosting when local disk is not enough. |
| Validation | Zod at every external boundary | Runtime input validation protects Server Actions, route handlers, and webhooks. |
| Tests | Vitest for units, Playwright for flows | Fast logic checks plus realistic browser coverage for SaaS-critical paths. |

Do not silently swap the stack. A stack change needs a short note in the PR because it changes deployment, migration, and debugging rules.

## Golden workflow

Always run the smallest relevant check before editing more code, then run the full check before the PR.

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm lint
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm e2e
pnpm build
```

If a script is missing, add it to `package.json` rather than inventing ad hoc commands in PR notes. Scripts are part of the project contract.

Recommended scripts:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:watch": "vitest",
  "e2e": "playwright test",
  "db:generate": "drizzle-kit generate",
  "db:migrate": "drizzle-kit migrate",
  "db:studio": "drizzle-kit studio",
  "db:seed": "tsx src/db/seed.ts"
}
```

## Folder structure

Use this shape unless the repository already has a stronger convention.

```text
src/
  app/                    # App Router pages, layouts, route handlers, Server Actions near routes
    (auth)/               # Sign-in, sign-up, password reset, invite acceptance
    (dashboard)/          # Authenticated product surface
    api/                  # Route handlers for webhooks and external integrations
  components/
    ui/                   # Primitive reusable components only
    forms/                # Form components paired with schemas/actions
    marketing/            # Public landing-page sections
  config/                 # Typed constants; no secrets
  db/
    client.ts             # Driver selection and Drizzle client
    schema.ts             # Tables, relations, enums
    migrations/           # Generated SQL committed to git
    seed.ts               # Idempotent local/dev seed data
  features/               # Product domains: billing, teams, projects, notifications
    <feature>/
      actions.ts          # Server Actions for this feature
      queries.ts          # Read-only DB accessors
      mutations.ts        # Write DB helpers used by actions/routes
      schema.ts           # Zod input/output schemas
      components/         # Feature-specific components
      tests/              # Unit/integration tests for the feature
  lib/                    # Framework-agnostic helpers
  server/                 # Auth/session, permissions, rate limits, jobs
  styles/                 # Global CSS and design tokens
  tests/                  # Cross-feature test setup and fixtures
```

Keep route folders thin. Business logic belongs in `features/*`, `server/*`, or `db/*` so it can be tested without rendering a page.

## Naming conventions

| Thing | Rule | Reason |
| --- | --- | --- |
| Files | `kebab-case.tsx` for components, `camelCase.ts` only for framework-required names | Kebab-case scans well in route-heavy apps. |
| React components | `PascalCase` export from a matching file | Makes imports predictable and grep-friendly. |
| Server Actions | Verb phrases ending in `Action`, for example `createTeamAction` | Separates UI event handlers from server mutations. |
| Queries | Noun or question form, for example `getTeamBySlug`, `listUserProjects` | Signals read-only behavior. |
| Mutations | Verb phrases, for example `createProject`, `archiveInvite` | Makes writes obvious in review. |
| Zod schemas | End with `Schema`, for example `createProjectSchema` | Keeps runtime validation visible. |
| DB tables | Plural snake_case in SQL, camelCase exports in TypeScript | SQL stays conventional while TypeScript remains idiomatic. |
| Env vars | Upper snake case and documented in `.env.example` | Prevents hidden deployment requirements. |

Prefer named exports. Default exports are allowed only for Next.js files that require them, such as `page.tsx`, `layout.tsx`, `loading.tsx`, and `error.tsx`.

## TypeScript rules

- Keep `strict` enabled. Reason: SaaS bugs usually happen at data boundaries, and strict mode catches nullable session, billing, and DB states.
- Do not use `any`. Use `unknown` plus parsing when data crosses a boundary. Reason: `any` bypasses the safety this template is trying to buy.
- Use `satisfies` for config objects. Reason: it validates shape without widening useful literals.
- Model IDs as branded strings when they cross domains. Reason: it prevents passing a `userId` where a `teamId` is expected.
- Keep server-only modules behind `import 'server-only'`. Reason: it prevents secrets and DB clients from entering client bundles.
- Put browser-only helpers behind `import 'client-only'` or inside Client Components. Reason: it avoids hydration and runtime environment bugs.

## App Router rules

- Pages are Server Components by default. Reason: less client JavaScript and direct access to server-side data.
- Add `'use client'` only for state, effects, browser APIs, or interactive event handlers. Reason: client boundaries are expensive and contagious.
- Fetch data in pages/layouts through `features/*/queries.ts`. Reason: route files stay readable and query code stays testable.
- Use route handlers for external protocols, webhooks, and machine clients. Reason: UI navigation and API contracts evolve differently.
- Use Server Actions for form-backed product mutations. Reason: they keep validation, auth, and mutation close to the UI without building needless JSON endpoints.
- Wrap mutations in `revalidatePath` or `revalidateTag` intentionally. Reason: stale dashboard data is a real product bug.

## Database and migration rules

### Schema location

Keep all Drizzle table definitions in `src/db/schema.ts` until the file becomes hard to navigate. Split by domain only after there are enough tables to justify it, then re-export from `src/db/schema.ts`.

### Driver boundary

`src/db/client.ts` is the only file that chooses between local `better-sqlite3` and Turso/libSQL.

Rules:

- Application code imports `db` from `src/db/client.ts`, never a raw driver. Reason: local and hosted SQLite stay interchangeable.
- Migrations must work against a local SQLite file first. Reason: CI and contributors need a zero-service path.
- Turso/libSQL settings live in env vars and are documented in `.env.example`. Reason: hidden cloud config blocks deployment.

### Migration discipline

- Generate migrations with `pnpm db:generate`; apply with `pnpm db:migrate`.
- Commit generated SQL migration files.
- Never edit an applied migration. Add a new migration instead.
- Do not use `push` commands in shared environments. Reason: schema drift becomes unreviewable.
- Every migration that touches existing data needs a reversible note in the PR. Reason: rollback risk is a product risk, not a tooling detail.
- Add indexes for foreign keys and high-cardinality lookup columns used in dashboards. Reason: SQLite can be fast, but only when access patterns are explicit.
- Use transactions for multi-step writes. Reason: SaaS state like team creation, invites, and billing records must not partially apply.

### Data modeling defaults

- Every table has `id`, `createdAt`, and `updatedAt` unless it is a pure join table.
- Use `deletedAt` for recoverable user-facing records. Use hard deletes only for short-lived tokens and cache rows.
- Store money in integer minor units plus currency, never floating point.
- Store external provider IDs as text with a unique index scoped to the provider.
- Keep audit logs append-only. Reason: support and billing investigations need history.

## Validation and security

- Parse every Server Action input with Zod before checking business rules. Reason: business logic should never see unknown shapes.
- Check authentication before authorization, then authorize against the resource being changed. Reason: user-level checks are not enough in team SaaS.
- Use a per-route permission helper for dashboard actions. Reason: duplicated `if` checks rot.
- Treat all webhook bodies as untrusted until signature verification passes. Reason: webhooks are public endpoints.
- Do not log secrets, session tokens, provider payloads, or full webhook bodies. Reason: logs are copied into support tools and CI artifacts.
- Use rate limits for auth, invites, magic links, and AI-generated endpoints. Reason: these are abuse magnets.
- Keep secrets out of `src/config`. Use env accessors that fail fast at startup or first server use.

## Component patterns

- UI primitives in `components/ui` know nothing about the database, auth, or billing. Reason: they should be reusable and easy to test.
- Feature components may import feature queries, schemas, and actions. Reason: product code can be cohesive inside a domain.
- Form components colocate with their Zod schema and Server Action. Reason: forms break when validation and mutation drift apart.
- Prefer composition over boolean prop explosions. Reason: SaaS dashboards accumulate states quickly.
- Keep loading and empty states explicit. Reason: most perceived quality issues are missing states, not missing features.
- Use accessible labels, landmarks, and keyboard paths from the first implementation. Reason: retrofitting accessibility is slower and riskier.

## API and Server Action patterns

For each mutation:

1. Parse input with Zod.
2. Read the current session.
3. Authorize against the target resource.
4. Execute the mutation in a transaction when more than one row changes.
5. Revalidate the affected path or tag.
6. Return a typed success/error shape; do not throw for expected validation errors.

Expected action result shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; code: string; message: string; fieldErrors?: Record<string, string[]> };
```

Reason: UI code can render predictable errors without parsing thrown exceptions.

## Testing expectations

- Unit test pure helpers, Zod schemas, permission helpers, and DB mapping logic.
- Integration test Server Actions with a temporary SQLite database.
- E2E test signup, login, team creation, billing gate behavior, and the primary dashboard flow.
- Add a regression test for every bug fix. Reason: SaaS regressions are usually permission, migration, or state bugs.
- Do not mock the database in tests that claim to verify persistence. Use an isolated SQLite file.

## What we do not do

| Avoid | Reason |
| --- | --- |
| Do not add Prisma to this template | Drizzle keeps SQL and migrations explicit for SQLite; mixing ORMs creates migration ambiguity. |
| Do not put DB calls inside Client Components | It leaks server concerns and will fail at runtime. |
| Do not create generic `utils.ts` dumping grounds | Ownership disappears; put helpers in the nearest domain. |
| Do not use API routes for every form | Server Actions are simpler for app-owned mutations. |
| Do not commit `.env`, local SQLite databases, or generated secrets | They leak credentials and create noisy diffs. |
| Do not swallow errors with `catch {}` | Silent failures become support tickets. |
| Do not add dependencies for one-line helpers | Dependency surface is security and maintenance surface. |
| Do not store dates as ambiguous local strings | Use UTC timestamps and format at the edge. |
| Do not trust AI-generated migrations without review | Schema changes are durable and hard to unwind. |

## Pull request checklist

Before opening a PR:

- [ ] The change follows the folder ownership rules.
- [ ] All external inputs are parsed with Zod.
- [ ] DB changes include generated migrations and a rollback note.
- [ ] Auth and authorization are both covered for protected mutations.
- [ ] Empty, loading, and error states are handled.
- [ ] `pnpm typecheck`, `pnpm lint`, `pnpm test`, and `pnpm build` pass or the PR explains the exact blocker.
- [ ] `.env.example` documents any new variable.
- [ ] No secrets, local database files, or provider payloads are committed.

## Default response behavior for Claude Code

- Start by reading `package.json`, `src/db/schema.ts`, and the files in the target feature.
- State the smallest safe plan before editing.
- Prefer minimal diffs that preserve established conventions.
- If a request is ambiguous but not dangerous, choose the convention in this file and continue.
- Ask before destructive actions, dependency swaps, migration rewrites, or auth/billing behavior changes.
- After editing, report changed files, commands run, and any checks that could not be run.
