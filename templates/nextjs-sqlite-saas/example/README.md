# Next.js SQLite SaaS Example

This small scaffold demonstrates the conventions from the sibling
`CLAUDE.md` in executable form.

It is intentionally dependency-free so the database rules can be verified with
Node 24+'s built-in `node:sqlite` module. The production template still supports
Node 20+ with `better-sqlite3` or Turso/libSQL; this example uses `node:sqlite`
only to make validation self-contained:

```bash
npm run validate
```

The validation script applies the migration, inserts related rows, verifies
foreign key enforcement, checks `ON DELETE CASCADE`, and confirms that default
timestamps are stored as ISO 8601 UTC text.

Files map to the template rules:

- `db/migrations/0001_init.sql` - numbered, forward-only SQLite migration.
- `db/migrate.mjs` - transaction-wrapped migration runner.
- `db/queries/users.mjs` and `db/queries/workspaces.mjs` - database access
  helpers kept outside React components.
- `lib/validation/workspaces.mjs` - server-side input validation.
- `app/actions/create-workspace-action.mjs` - narrow Server Action shape.
- `app/(app)/dashboard/page.tsx` - Server Component composition sketch.
