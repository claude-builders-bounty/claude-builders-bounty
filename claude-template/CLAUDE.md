# Project rules

Next.js 15 App Router SaaS with one SQLite file through better-sqlite3. These rules are the default for a new repo. Do not ask which stack to use.

## Stack and versions

- next 15, app router only. Do not add a pages router.
- react 19, typescript strict.
- better-sqlite3 for the database. One file at data/app.db. Do not add a hosted database.
- SQL migrations are plain files. Do not add an ORM or a query builder.
- Tailwind is the only styling system. Do not add a second component library.

## Folder structure

```
app/(public)/page.tsx          marketing routes
app/(app)/app/page.tsx         signed-in product routes
app/api/health/route.ts        route handlers
components/                    server components by default
lib/db.ts                      the only module that opens SQLite
lib/auth.ts                    session cookie helpers
db/migrations/0001_init.sql    ordered SQL files
db/migrate.ts                  applies pending files inside a transaction
data/app.db                    created at runtime, never committed
```

A route group in parentheses does not appear in the URL. Product pages live under /app. Public pages live at /.

## Commands

```
npm install
npm run dev
npm run migrate
npm run typecheck
npm run build
```

`npm run migrate` is the only way schema changes reach the database. Do not apply SQL by hand against data/app.db.

## Names

- Files and folders: lowercase with hyphens, except React component files which use PascalCase.
- SQL tables and columns: snake_case, plural tables.
- TypeScript functions: camelCase. Types: PascalCase.
- Route handlers export GET, POST, PATCH, or DELETE. Do not export a custom action name from a route file.

## Database and migrations

- A migration file is immutable after it has been merged. A change is a new file with the next number.
- The runner records the filename in schema_migrations. A file that is already recorded is never executed again.
- Every migration runs inside one transaction. A failed file rolls back.
- Foreign keys are declared in SQL. The connection executes PRAGMA foreign_keys = ON before any query.
- better-sqlite3 is synchronous. Do not wrap a query in a promise and do not call it from an edge runtime. Node.js runtime only.
- User input reaches SQL only through bound parameters. Do not concatenate a request value into a statement.
- Store money as integer cents. Store instants as ISO-8601 text in UTC.

## Components

- A component is a server component unless it needs state or a browser event. Add "use client" only on that leaf, not on a layout.
- A form posts to a server action in the same feature folder. The action validates input, writes through lib/db.ts, then calls revalidatePath.
- Read session state on the server from the cookie. Do not put an access token in localStorage.
- One component owns one visible region. Do not fetch inside a shared visual primitive.

## Do not

- Do not add Prisma, Drizzle, or Knex. The migration runner and bound SQL are the data layer. A second layer hides the SQL that needs review.
- Do not open the database in a component file. lib/db.ts owns the connection so the pragma and the path exist in one place.
- Do not edit a merged migration. The checksum record would disagree with the file on the next machine.
- Do not store the database in the repo or in public/. It contains user rows.
- Do not use the edge runtime for a route that touches SQLite. better-sqlite3 needs Node.js.
- Do not add a pages/ directory. The app router is the only router, so there is one place to look for a URL.
