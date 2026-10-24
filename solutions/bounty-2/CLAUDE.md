# CLAUDE.md — Next.js 15 + SQLite SaaS

These instructions apply to a greenfield SaaS using Next.js 15 App Router, TypeScript, and SQLite through `better-sqlite3` or Turso/libSQL. Follow the repository's existing conventions when they differ.

## Project layout

- `src/app/`: routes, layouts, loading and error boundaries. Keep route files thin.
- `src/components/`: reusable UI; use PascalCase component filenames.
- `src/lib/`: server-only business logic, database access, auth, and validation.
- `src/db/`: schema, migrations, and seed scripts.
- `src/actions/`: server actions; validate every input at the boundary.
- `tests/`: unit and integration tests; mirror the source layout.
- `public/`: static assets only.

## Commands

Use the package manager indicated by the lockfile; do not create a second lockfile.

- `npm run dev`: local development.
- `npm run build`: production build.
- `npm run lint`: lint.
- `npm run typecheck`: TypeScript checks.
- `npm test`: tests.
- `npm run db:migrate`: apply migrations.
- `npm run db:status`: inspect migration state.

If a script is absent, inspect `package.json` and report that rather than inventing a command.

## Database rules

1. All schema changes must be additive migrations committed with the code change.
2. Never edit an already-applied migration. Add a new migration with a sortable timestamp or sequence.
3. Keep migrations transactional when SQLite supports the operation; document rebuild-table migrations.
4. Enable foreign keys on every SQLite connection with `PRAGMA foreign_keys = ON`.
5. Bind SQL parameters. Never interpolate user-controlled values into SQL strings.
6. Add indexes for foreign keys and frequent filter/order columns; justify each index.
7. Store timestamps in UTC using one documented representation.
8. Do not use a single SQLite connection concurrently across unsafe async boundaries. For Turso, follow the driver's transaction API.
9. Test migrations against both an empty database and a copy of the previous schema.
10. Never run destructive migrations against production from an agent session.

## Next.js and TypeScript

- Default to Server Components; add `"use client"` only for browser state, effects, or event handlers.
- Keep secrets and database clients in server-only modules. Never import them from client components.
- Use route handlers for HTTP APIs and server actions for form mutations; do not duplicate business logic.
- Validate request data with the project's schema library before authorization-sensitive work.
- Check authentication and resource ownership on the server for every read or mutation.
- Return explicit loading, empty, and error states. Do not swallow exceptions.
- Avoid `any`; prefer narrow types and discriminated unions.
- Use stable, accessible labels and semantic HTML.

## Security and privacy

- Treat all form fields, query parameters, uploaded files, and external API responses as untrusted.
- Authorize before fetching or mutating private records.
- Never log passwords, session tokens, API keys, or full sensitive payloads.
- Use environment variables for secrets and update `.env.example` with names only.
- Add rate limits to expensive or abuse-prone endpoints.
- Do not disable CSRF, origin checks, or authentication to make tests pass.

## Tests and completion checklist

- Add regression tests for every bug fix and boundary condition.
- Test unauthenticated, unauthorized, malformed, empty, and duplicate inputs where relevant.
- Run lint, typecheck, tests, and production build for changed areas.
- Review the final diff for secrets, generated files, unrelated formatting, and migration safety.
- Update documentation and `.env.example` when configuration changes.
- Summarize changed behavior, commands run, and any checks that could not be run.
