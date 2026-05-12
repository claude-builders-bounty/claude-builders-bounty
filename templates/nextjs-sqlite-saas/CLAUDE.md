# CLAUDE.md - Next.js + SQLite SaaS

Use this file as the project instructions for a small SaaS product built with
Next.js App Router, TypeScript, SQLite, and server-side API routes.

## Project Shape

- Framework: Next.js 15 with the App Router.
- Language: TypeScript in strict mode.
- Database: SQLite stored at `./data/app.db` for local development.
- DB access: use a single server-only helper module in `src/lib/db.ts`.
- Auth: keep auth behind `src/lib/auth.ts`; use a placeholder user in local
  development until a real provider is configured.
- UI: use accessible React components, semantic HTML, and server components by
  default. Add client components only for browser-only interactivity.

## Setup Commands

Run these commands when starting from a clean checkout:

```bash
npm install
npm run db:migrate
npm run dev
```

Expected package scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:seed": "tsx scripts/seed.ts"
  }
}
```

## Database Rules

- Keep schema migrations in `migrations/` as numbered SQL files, for example
  `001_create_users.sql`.
- Run migrations from `scripts/migrate.ts`; do not create tables ad hoc inside
  route handlers.
- Enable foreign keys for every SQLite connection with `PRAGMA foreign_keys = ON`.
- Use prepared statements for all user input.
- Keep timestamps as ISO strings in UTC.

Reason: migrations make schema changes reviewable, repeatable, and easy for
Claude to reason about when adding new features.

## API Route Rules

- Place API routes under `src/app/api/**/route.ts`.
- Validate every request body before touching the database.
- Return JSON with a stable shape:

```ts
type ApiSuccess<T> = { ok: true; data: T };
type ApiFailure = { ok: false; error: { code: string; message: string } };
```

- Use correct HTTP status codes: `400` for validation, `401` for unauthenticated,
  `403` for unauthorized, `404` for missing resources, and `500` only for
  unexpected server errors.
- Never leak raw database errors to the client.

Reason: a consistent response contract keeps UI code simple and prevents one-off
error handling paths.

## Auth Placeholder

Until real authentication is added, use this local helper:

```ts
export async function requireUser() {
  return {
    id: "dev-user",
    email: "dev@example.com",
    role: "owner" as const,
  };
}
```

Rules:

- Route handlers must call `requireUser()` before reading or writing private
  tenant data.
- Keep the placeholder in one file so it can be replaced with Clerk, Auth.js, or
  another provider later.
- Never spread placeholder auth logic across pages, components, or migrations.

Reason: isolating auth avoids rewrites when the SaaS moves from local prototype
to production authentication.

## Feature Workflow

For every feature:

1. Add or update the migration first.
2. Add the server-only database helper functions.
3. Add the API route or server action.
4. Add the UI.
5. Add focused tests for validation and database behavior.
6. Run `npm run typecheck`, `npm run lint`, and `npm run build`.

## Testing Rules

- Prefer unit tests for pure validation functions.
- Prefer integration tests for API routes and database helpers.
- Use a temporary SQLite database for tests instead of the development database.
- Seed only the records required by the test.

Reason: SQLite tests are cheap, so regressions should be caught at the database
boundary rather than only in UI flows.

## Code Style

- Keep server-only utilities in `src/lib/`.
- Add `import "server-only"` at the top of database and auth modules.
- Do not import database helpers from client components.
- Prefer explicit types for database rows and API responses.
- Keep route handlers small; move reusable logic into `src/lib/`.
- Avoid adding dependencies unless they remove substantial code or risk.

## Safety Checklist Before Completing Work

- `npm run typecheck` passes.
- `npm run lint` passes.
- `npm run build` passes.
- New migrations run on a clean database.
- API routes validate malformed input.
- No secrets are committed.
- No client component imports `src/lib/db.ts`.
