# CLAUDE.md

This project is a production SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React. Treat the database as local-first infrastructure: keep schema changes explicit, keep reads close to the route that needs them, and avoid adding services before the product needs them.

## Stack & Versions

- Next.js 15 with the App Router in `app/`
- React Server Components by default
- TypeScript in strict mode
- SQLite through `better-sqlite3` for single-node apps or Turso/libSQL for hosted SQLite
- Tailwind CSS and small local UI components
- Vitest for unit tests and Playwright for user flows

Reason: this stack keeps a greenfield SaaS simple enough to ship while still allowing real authentication, billing, dashboards, and background jobs.

## Dev Commands

Use these commands unless the project README overrides them:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:migrate
```

Before reporting a change as done, run the narrowest useful check. For UI or routing changes, run `npm run lint` and open the affected page. For schema or query changes, run `npm run db:migrate` and the tests touching that data.

## Folder Structure

Use this shape for new code:

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
db/
  migrations/
  schema.ts
  client.ts
  queries/
lib/
  auth/
  billing/
  email/
  jobs/
tests/
```

Keep route-specific code inside its route folder. Move code to `components/`, `db/queries/`, or `lib/` only after it is reused. Reason: premature shared folders hide product behavior and make SaaS flows harder to review.

## Naming Conventions

- Route folders use kebab-case: `billing-settings`, `team-members`.
- React components use PascalCase: `PlanSelector.tsx`.
- Server actions end in `.action.ts`.
- Database query files name the business object: `subscriptions.ts`, `teams.ts`.
- Test files sit beside the thing they test or under `tests/` for full flows.

Use names from the product domain rather than technical names. Prefer `createTeamSubscription` over `insertStripeRow`.

## SQL & Migration Rules

- Every schema change gets a migration file in `db/migrations/`.
- Migration filenames use sortable timestamps: `202605140900_add_team_members.sql`.
- Migrations must be forward-only. Do not edit a migration after it has shipped.
- Always use explicit column lists in `INSERT` statements.
- Use foreign keys for ownership boundaries such as `team_id`, `user_id`, and `subscription_id`.
- Add indexes when a query filters by tenant, owner, status, or created date.
- Store money as integer cents and timestamps as ISO strings or Unix milliseconds, consistently across the app.

Reason: SQLite is reliable when schema changes are boring, explicit, and easy to replay from an empty database.

## Data Access Patterns

- Read data in Server Components when the data is needed to render a page.
- Use Server Actions for form submissions that mutate app data.
- Keep SQL in `db/queries/`; route handlers should orchestrate, not build long SQL strings inline.
- Validate external input at the route/action boundary.
- Do not validate values that came directly from typed internal functions.
- Return plain objects from query functions, not database driver rows that leak implementation details.

For tenant-owned data, every query must include the tenant or team scope. A query that reads `projects` without `team_id` is a bug unless it is an admin-only path.

## Component Patterns

- Prefer Server Components. Add `"use client"` only for state, effects, browser APIs, or interactive controls.
- Keep client components small and pass them plain serializable props.
- Forms should render validation errors next to the field and keep submit buttons disabled only while submitting.
- Use shared UI primitives for buttons, inputs, dialogs, dropdowns, and tables.
- Keep dashboard screens dense and scannable. SaaS users return to complete work, not to read marketing copy.

Reason: server-first UI reduces client bundle size and keeps product pages close to the data they show.

## Authentication & Authorization

- Authentication answers "who is this user?"
- Authorization answers "can this user act on this team/resource?"
- Check authorization on the server for every mutation and private read.
- Never rely on hidden buttons or client-side redirects as the only protection.
- Keep session helpers in `lib/auth/` and permission checks near the data access they protect.

## Billing Rules

- Billing webhooks are external input. Verify signatures before reading the body.
- Webhook handlers should be idempotent.
- Store the provider ID and the internal owner ID together.
- Do not unlock paid features from the checkout redirect alone; wait for the verified webhook or provider lookup.

## What We Do Not Do

- Do not add a generic repository layer. SQLite queries are already the abstraction.
- Do not introduce background job infrastructure for work that can run during a request.
- Do not add global state for server data. Fetch it on the server.
- Do not create reusable components before the second real use.
- Do not hide failed migrations with fallback code. Fix the migration.
- Do not add compatibility shims for code that has not shipped.

Each of these rules keeps the app easier to ship and easier to debug.

## Before Finishing

Confirm the change against the actual product path:

- Run the relevant command from the Dev Commands section.
- For UI changes, open the page and complete the main action.
- For data changes, inspect the resulting row or migration output.
- For billing, auth, or webhook work, test the failure path and the success path.

Report only what changed, what was checked, and anything still blocked.
