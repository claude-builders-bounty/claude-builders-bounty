# CLAUDE.md

This file gives Claude Code project-specific instructions for a production
Next.js 15 App Router application backed by SQLite. Follow these rules when
reading, editing, testing, or reviewing this repository.

## Project Assumptions

- Runtime: Node.js 20 LTS or newer.
- Framework: Next.js 15 using the App Router in `app/`.
- Language: TypeScript with `strict` enabled.
- UI: React Server Components by default, Client Components only where browser
  state, effects, or event handlers are required.
- Database: SQLite for local and single-node deployments, with either
  `better-sqlite3` for file-backed SQLite or `@libsql/client` for Turso/libSQL.
- Migrations: SQL-first migrations generated or managed by the repository's
  chosen migration tool, such as Drizzle Kit.
- Validation: Zod or an equivalent schema validator at every trust boundary.

If the repository already has a different tool for one of these concerns, keep
the existing tool and follow the same principles. Do not introduce a second ORM,
migration system, validator, test runner, or styling framework unless a task
explicitly asks for that migration.

## How To Work In This Repository

Before making changes:

1. Read the nearest existing code for the same feature area.
2. Check `package.json` scripts before inventing commands.
3. Check the current database layer before adding new data access helpers.
4. Prefer a small change that fits the existing architecture over a broad
   cleanup.
5. Keep generated files, lockfiles, migrations, and snapshots out of the diff
   unless the task requires them.

When editing:

- Make Server Components the default for pages, layouts, and data-loading
  components.
- Keep business rules on the server side, close to server actions, route
  handlers, or service functions.
- Keep Client Components small and focused on interaction.
- Validate all form data, route params, query params, cookies, and request
  bodies before using them.
- Use parameterized SQL or query-builder placeholders for every database value.
- Add or update focused tests when behavior changes.

## Repository Structure

Use this structure unless the repository already has a clear equivalent:

```text
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
  client.ts
  schema.ts
  migrations/
features/
  <feature-name>/
    actions.ts
    queries.ts
    schema.ts
    components/
    tests/
lib/
  auth.ts
  env.ts
  errors.ts
  result.ts
server/
  services/
  jobs/
tests/
  setup.ts
```

Directory responsibilities:

- `app/`: routes, layouts, route handlers, loading states, error boundaries, and
  page composition.
- `components/ui/`: reusable presentational primitives without business rules.
- `features/<feature>/`: feature-owned server actions, queries, validation
  schemas, and feature-specific components.
- `db/`: database client creation, schema declarations, and migrations.
- `lib/`: shared helpers that do not belong to a single feature.
- `server/`: background jobs, integration clients, and service orchestration
  that should never be imported by Client Components.
- `tests/`: cross-feature test setup and utilities.

Do not put database queries directly in generic UI components. Keep database
access in route handlers, Server Components, server actions, feature query
modules, or service modules.

## Naming Conventions

- Components: `PascalCase.tsx`, for example `InvoiceTable.tsx`.
- Hooks: `use-kebab-name.ts` or `useCamelName.ts`, following the local style.
- Server actions: verb-first names such as `createInvoice`,
  `archiveCustomer`, or `updateProfile`.
- Query helpers: descriptive read names such as `getInvoiceById`,
  `listCustomersForWorkspace`, or `countOpenTasks`.
- Validation schemas: suffix with `Schema`, for example `createInvoiceSchema`.
- Database tables: plural snake_case, for example `users`, `workspaces`,
  `invoice_items`.
- Database columns: snake_case, for example `created_at`, `workspace_id`,
  `deleted_at`.
- Route segments: lowercase kebab-case.

Use domain names in identifiers. Avoid vague names such as `data`, `item`,
`manager`, `helper`, or `utils` when the domain concept has a real name.

## Commands

Use the real scripts from `package.json`. If these scripts exist, prefer them:

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run db:generate
npm run db:migrate
npm run db:studio
npm run db:seed
```

Before opening a pull request, run the smallest meaningful validation for the
change:

- Documentation-only change: `npm run lint` if Markdown linting exists, or a
  manual link and formatting check.
- Type-only or component change: `npm run typecheck` and `npm run lint`.
- Server behavior change: `npm run test` plus `npm run typecheck`.
- Database or route behavior change: migration check, focused tests, and
  `npm run build`.

If a command cannot run because dependencies or services are unavailable, say so
in the PR and include the exact command and error.

## Environment Variables

Declare and validate environment variables in one server-only module, usually
`lib/env.ts`.

Rules:

- Never read `process.env` throughout the codebase.
- Never expose secrets through `NEXT_PUBLIC_*`.
- Keep public browser variables separate from server-only variables.
- Validate required variables at startup with clear error messages.
- Use `.env.example` to document required variables without real secrets.

Example categories:

```text
DATABASE_URL=file:./local.db
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## SQLite And Turso Rules

SQLite is reliable when the application respects its constraints. Treat these
rules as production requirements:

- Enable foreign keys for every connection.
- Use WAL mode for local file-backed SQLite when supported.
- Configure a busy timeout for file-backed SQLite to avoid avoidable write
  failures under light concurrency.
- Keep write transactions short.
- Do not hold transactions open across network calls, file uploads, email
  sends, AI calls, or third-party API calls.
- Use explicit transactions for multi-table writes that must succeed or fail
  together.
- Store money in integer minor units, such as cents.
- Store booleans as `0` or `1` if the ORM does not provide a native mapping.
- Store timestamps consistently, preferably ISO strings or integer epoch
  milliseconds. Do not mix formats in one table.
- Add indexes for foreign keys and common filters used by list pages.
- Use cursor pagination for unbounded lists.
- Avoid `SELECT *` in feature queries that feed user-facing pages.

For Turso/libSQL:

- Keep database access server-side.
- Do not import Turso clients into Client Components.
- Expect network latency and handle transient failures at service boundaries.
- Do not assume local file locking behavior applies to hosted libSQL.

## Database Migrations

Migrations are production artifacts. Handle them carefully.

- Never edit a migration that has already been applied outside local throwaway
  development.
- Prefer additive migrations: create table, add nullable column, backfill, then
  enforce constraints in a later step if necessary.
- Include rollback notes in the PR when a migration is risky, even if the tool
  does not support automatic down migrations.
- Preserve existing data unless the task explicitly asks for deletion.
- Do not drop columns, rename columns, or rewrite tables without calling out
  the data impact.
- Keep seed data separate from schema migrations unless the seed data is
  required for the schema to function.
- Make multi-table data repairs idempotent.

When adding a table, include:

- A primary key.
- Required foreign keys.
- `created_at` and `updated_at` when records are user- or system-managed.
- Indexes for common access paths.
- A uniqueness constraint for natural uniqueness rules.

## Server Components, Client Components, And Actions

Default to Server Components.

Use a Client Component only when the component needs:

- `useState`, `useEffect`, or browser-only APIs.
- Event handlers such as `onClick` or `onChange`.
- Client-side animation state.
- Optimistic UI that cannot be handled at the form boundary.

Server action rules:

- Put `"use server"` actions in feature-owned `actions.ts` files or next to the
  route when the action is route-specific.
- Validate inputs with a schema before checking permissions or writing data.
- Re-check authorization inside the action.
- Return typed success and failure states that forms can render.
- Revalidate the smallest useful path or tag after writes.
- Do not leak raw database errors to users.

Route handler rules:

- Use route handlers for webhooks, machine-facing APIs, uploads, and integration
  endpoints.
- Validate method, authentication, authorization, and body shape.
- Return stable JSON error shapes.
- Avoid duplicating business logic between route handlers and server actions;
  move shared rules into a server-only service function.

## Validation And Error Handling

Validate data at every trust boundary:

- User-submitted forms.
- Route params and search params.
- Request JSON bodies.
- Webhook payloads.
- Environment variables.
- Data returned by third-party APIs if it affects writes or permissions.

Error handling rules:

- Use expected error types for validation, authorization, not-found, and
  conflict cases.
- Log unexpected server errors with useful context, but never log secrets.
- Show user-safe messages in UI.
- Keep raw SQL, tokens, stack traces, and provider payloads out of client
  responses.

## Authentication And Authorization

Do not trust the browser for permissions.

- Check authentication in server actions, route handlers, and protected Server
  Components.
- Check authorization against the resource being accessed, not only against the
  current route.
- Scope list queries by the current user, workspace, organization, or tenant.
- Enforce ownership and role checks before every write.
- Do not rely on hidden form fields for user IDs, prices, roles, or ownership.
- Treat admin operations as separate code paths with explicit checks.

## Data Fetching And Caching

- Fetch data in Server Components when it is needed for initial render.
- Keep mutations in server actions or route handlers.
- Use `cache`, `revalidatePath`, `revalidateTag`, or `unstable_noStore` only
  when the repository already uses those patterns or the caching behavior is
  clear.
- Do not cache user-specific or permission-sensitive data without a user- or
  tenant-scoped cache key.
- Avoid duplicate queries across a page by lifting shared reads to the nearest
  common Server Component.

## Forms

Forms should work with server actions unless the UX requires a client-only flow.

Form rules:

- Validate on the server even when client validation exists.
- Preserve submitted values after validation failures when practical.
- Render field-level errors where users can act on them.
- Disable submit buttons only while a request is pending.
- Use optimistic UI only for reversible, low-risk interactions.
- Protect destructive actions with clear confirmation UI.

## Testing

Use the repository's existing test tools. If no test tools exist yet, prefer:

- Vitest for unit and server-side tests.
- React Testing Library for interactive Client Components.
- Playwright for critical browser flows.
- A temporary SQLite database per test file or test worker for data tests.

Testing rules:

- Test business rules at the service/action level, not only through UI.
- Test migrations or schema changes with a fresh database.
- Test authorization failures for reads and writes that touch private data.
- Use factories or builders for test data instead of large shared fixtures.
- Keep tests deterministic; do not depend on wall-clock time without a fake
  clock.

For SQLite tests:

- Use an isolated database file or in-memory database per test scope.
- Enable foreign keys in tests.
- Clean up database files after tests.
- Do not point tests at a developer's real local database.

## Security Rules

- Never commit secrets.
- Never concatenate user input into SQL.
- Never evaluate user-provided code.
- Sanitize or validate URLs before redirects.
- Validate webhook signatures before processing webhook bodies.
- Use secure, HTTP-only cookies for session tokens.
- Do not expose server-only modules to Client Components.
- Keep file uploads size-limited and type-checked.
- Treat AI-generated content as untrusted input before rendering or storing it.

## Performance Rules

- Avoid N+1 database queries in list pages.
- Add pagination before a table can grow without bounds.
- Select only fields needed by the UI.
- Keep large, rarely changing data out of Client Component props.
- Use streaming and loading states for slow server reads.
- Use transactions to reduce partial writes, not as a substitute for batching
  unrelated work.
- Measure before adding complex caching.

## Accessibility Rules

- Use semantic HTML before custom ARIA.
- Keep labels connected to form controls.
- Preserve keyboard navigation for menus, dialogs, and custom controls.
- Maintain visible focus states.
- Do not use color alone to communicate state.
- Test important flows with keyboard-only navigation.

## Pull Request Expectations

Every PR should include:

- What changed.
- Why it changed.
- How it was tested.
- Any migration, rollback, or data-risk notes.
- Screenshots for visible UI changes.

For database changes, include:

- Migration file names.
- Whether the migration is additive or destructive.
- Expected runtime impact.
- Backfill or rollback notes.

## Anti-Patterns

Avoid these unless the task explicitly requires them:

- Adding `"use client"` to an entire page to fix one interactive widget.
- Reading or writing SQLite from a Client Component.
- Building SQL with string concatenation.
- Editing an applied migration instead of creating a new migration.
- Adding a new global state library for local component state.
- Creating generic `utils.ts` files for domain-specific logic.
- Duplicating the same validation schema in client and server files.
- Returning raw ORM records directly from public API routes.
- Swallowing errors with empty `catch` blocks.
- Making broad formatting-only changes in files unrelated to the task.
- Introducing a second database client or ORM.
- Running destructive data migrations without an explicit data-impact note.

## Claude Code Behavior

When working as Claude Code in this repository:

- State assumptions before changing architecture.
- Prefer existing local patterns over generic framework advice.
- Keep diffs small and task-focused.
- Ask before making destructive data, migration, or dependency changes.
- Do not modify generated files unless generation is part of the task.
- Do not update dependencies unless the task requires it.
- After editing, run the most relevant available validation command.
- If validation cannot run, report the exact blocker.
