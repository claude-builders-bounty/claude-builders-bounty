# CLAUDE.md

This project is a production-oriented SaaS built with Next.js 15 App Router, React 19, TypeScript, Tailwind CSS, Drizzle ORM, and SQLite. Use `better-sqlite3` for local development and Turso/libSQL for hosted production SQLite unless the project explicitly chooses one runtime.

## Stack & Versions

| Rule | Reason |
| --- | --- |
| Use Next.js 15 App Router only; do not add a Pages Router directory. | One routing model keeps layouts, data loading, and caching behavior predictable. |
| Use React Server Components by default. Add `"use client"` only for browser state, effects, refs, or event handlers. | Server Components reduce client JavaScript and keep database access on the server. |
| Use TypeScript `strict` mode and avoid `any`. | SaaS code carries billing, auth, and data ownership risks; weak types hide those mistakes. |
| Use Drizzle ORM for schema, queries, and migrations. | SQLite needs explicit schema history, and Drizzle keeps SQL visible without stringly typed data access. |
| Use `better-sqlite3` for local single-process development and Turso/libSQL for deployed environments. | Local SQLite is fast and deterministic; Turso gives hosted replication and connection management. |

## Dev Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Next.js dev server. |
| `npm run build` | Verify production compilation, type checking, and route analysis. |
| `npm run lint` | Run ESLint before every PR. |
| `npm run test` | Run unit and integration tests. |
| `npm run db:generate` | Generate Drizzle migrations from schema changes. |
| `npm run db:migrate` | Apply migrations to the configured SQLite database. |
| `npm run db:studio` | Inspect local data during development. |

If a script is missing, add it to `package.json` instead of inventing one-off commands in docs or PR notes.

## Folder Structure

```text
src/
  app/
    (marketing)/
    (app)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    layout/
  db/
    schema.ts
    client.ts
    migrations/
    queries/
  features/
    accounts/
    billing/
    projects/
  lib/
    auth.ts
    env.ts
    errors.ts
    ids.ts
  server/
    actions/
    services/
  tests/
```

| Rule | Reason |
| --- | --- |
| Put routes in `src/app`, not in feature folders. | App Router file conventions are easier to scan when route files stay in one tree. |
| Put reusable domain logic in `src/features/<domain>`. | SaaS domains such as billing and accounts evolve independently and should not leak through the whole app. |
| Put database schema in `src/db/schema.ts` and query helpers in `src/db/queries`. | Schema and reads/writes need a single ownership boundary to prevent migration drift. |
| Put mutations in `src/server/actions` or route handlers. | Server-only writes make auth checks, validation, and revalidation explicit. |
| Keep `src/components/ui` domain-free. | Base UI must not import billing, account, project, or database code. |

## Naming Conventions

| Rule | Reason |
| --- | --- |
| Use kebab-case for route segments and filenames that map to URLs. | URLs stay readable and consistent across platforms. |
| Use PascalCase for React components. | Component imports remain visually distinct from functions and data helpers. |
| Use camelCase for functions, variables, and Server Actions. | This matches TypeScript conventions and keeps action names readable in forms. |
| Use snake_case for database table and column names. | SQLite tooling and SQL queries remain conventional and easy to inspect. |
| Name Server Actions as verbs, for example `createProject` or `updateBillingEmail`. | Mutations should read like explicit commands. |
| Name query helpers as nouns or predicates, for example `getProjectById` or `listAccountMembers`. | Reads should be side-effect free by name. |

## App Router Rules

| Rule | Reason |
| --- | --- |
| In Next.js 15, treat `params` and `searchParams` as async in pages, layouts, and route handlers. Await them before reading values. | Next.js 15 moved dynamic request APIs to async access; synchronous reads can fail builds or prerendering. |
| Keep route pages thin: load data, choose layout, call feature components. | Thin route files make authorization and caching decisions easier to audit. |
| Use `loading.tsx`, `error.tsx`, and `not-found.tsx` at route boundaries. | SaaS users need predictable feedback for slow data, failures, and missing resources. |
| Use route groups such as `(marketing)` and `(app)` to separate public and authenticated surfaces. | Authenticated layouts often load user/account context that marketing pages should never pay for. |
| Use `revalidatePath` or `revalidateTag` immediately after successful mutations. | Stale dashboards create support issues and duplicate user actions. |

Example:

```tsx
type PageProps = {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ tab?: string }>;
};

export default async function ProjectPage({ params, searchParams }: PageProps) {
  const { projectId } = await params;
  const { tab = "overview" } = await searchParams;
  return <ProjectScreen projectId={projectId} tab={tab} />;
}
```

## SQL & Migration Conventions

| Rule | Reason |
| --- | --- |
| Change database shape only through Drizzle schema and generated migrations. | Hand-edited production SQLite schemas are hard to reproduce and rollback. |
| Never edit a migration after it has been merged. Create a new migration. | Applied migration history must stay append-only across developer machines and production. |
| Every table must have `id`, `created_at`, and `updated_at` unless it is a pure join table. | Auditing and support workflows need stable identity and timestamps. |
| Scope tenant-owned rows by `account_id` or equivalent. | Multi-tenant SaaS data leaks usually come from missing ownership filters. |
| Add indexes for foreign keys and common dashboard filters. | SQLite performs well when access patterns are explicit; hidden full scans hurt quickly. |
| Wrap multi-step writes in transactions. | Partial writes create billing, permissions, and onboarding inconsistencies. |
| Validate inputs before database writes with a schema library such as Zod. | Database constraints are the last line of defense, not the user-facing validation layer. |

Query pattern:

```ts
export async function getProjectForAccount(projectId: string, accountId: string) {
  return db.query.projects.findFirst({
    where: and(eq(projects.id, projectId), eq(projects.accountId, accountId)),
  });
}
```

## Component Patterns

| Rule | Reason |
| --- | --- |
| Prefer Server Components for screens, tables, and read-only views. | The server can fetch data directly and send less JavaScript. |
| Use Client Components only for interactive islands. | Small client boundaries preserve App Router performance. |
| Pass plain serialized props into Client Components. | Functions, database rows with methods, and complex classes do not cross the RSC boundary safely. |
| Keep forms close to their Server Action and validation schema. | Form behavior is easier to review when input, validation, mutation, and errors are co-located. |
| Use accessible native elements before custom widgets. | SaaS users rely on keyboard, screen readers, and predictable browser behavior. |
| Render empty, loading, and error states for every data-heavy component. | Blank dashboards look broken and cause repeated support tickets. |

## Auth, Permissions & Data Access

| Rule | Reason |
| --- | --- |
| Check authentication at the route layout boundary for authenticated groups. | One auth gate prevents accidental unauthenticated dashboard routes. |
| Check authorization inside every query or service that loads tenant data. | UI-level checks are not security boundaries. |
| Never trust `accountId`, `userId`, role, price, or plan values from client input. | These values control access and billing. Load them server-side. |
| Keep secrets in environment variables validated by `src/lib/env.ts`. | Missing secrets should fail boot, not fail mid-request. |
| Do not log tokens, session cookies, email verification links, or payment identifiers. | Logs are often broader access surfaces than production databases. |

## What We Do Not Do

| Anti-pattern | Why |
| --- | --- |
| Do not put database calls in Client Components. | It leaks server-only concerns and usually breaks bundling or security. |
| Do not add a second ORM or raw SQL layer for convenience. | Multiple data layers create inconsistent transactions and migration ownership. |
| Do not create generic `utils.ts` dumping grounds. | Shared utilities become unreviewable and hide domain coupling. |
| Do not use API routes for internal form mutations when Server Actions fit. | API routes add boilerplate and duplicate validation for same-app interactions. |
| Do not cache tenant-specific data without including tenant identity in the cache key. | Cross-tenant cache leaks are severe production incidents. |
| Do not silently catch database or payment errors. | SaaS workflows need explicit failure states and retry behavior. |
| Do not introduce global mutable singletons except the database client. | Shared mutable state breaks serverless and test isolation. |

## PR Expectations

Before opening a PR:

1. Run `npm run lint`, `npm run test`, and `npm run build`.
2. Run `npm run db:generate` when schema changes, and commit the generated migration.
3. Include screenshots or short notes for user-facing changes.
4. Mention any cache invalidation, migration, or auth behavior touched by the change.
