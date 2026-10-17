# VERIFIED — evidence log

Everything below was actually run, not reasoned about. Run `node verify.mjs` to replay the
static checks; the transcript is what the real project run produced.

## 1. Static checks — CLAUDE.md vs the scaffold it promises

```
$ node verify.mjs
... 53 checks ...
ALL PASS
```

Covers: every required section, every rule bullet carrying a `because`, every anti-pattern row
carrying a substantive reason, no unresolved placeholder, all 22 documented paths created by
`scaffold.sh`, all 9 documented npm scripts existing, the migration runner matching the doc, WAL
and `foreign_keys` pragmas present, no ORM.

## 2. Real project run — a genuinely scaffolded project

```
$ bash scaffold.sh /tmp/saas-test
scaffolded /tmp/saas-test: 24 files

$ npm install better-sqlite3 zod tsx

$ npm run db:migrate
applied 0001_init.sql
1 applied

$ npm run db:migrate          # second run must be a no-op
up to date

$ npm test
# tests 1
# pass 1
# fail 0

$ npm run db:reset
database removed
applied 0001_init.sql
1 applied

$ npm run db:new -- add_widgets
db/migrations/0002_add_widgets.sql

$ npm run db:migrate
applied 0002_add_widgets.sql
1 applied
```

## 3. Resulting schema — proof the migrations actually applied

```
objects: index:idx_invoices_user, index:idx_users_email,
         index:sqlite_autoindex__migrations_1, index:sqlite_autoindex_invoices_1,
         index:sqlite_autoindex_users_1, index:sqlite_autoindex_users_2,
         table:_migrations, table:invoices, table:users
```

## Bugs the real run caught, and the doc now encodes

These are the reason to run the scaffold rather than trust the prose:

1. **Nested transaction.** The runner opens a transaction per migration *and* the `.sql` files
   carried their own `BEGIN;`/`COMMIT;` →
   `SqliteError: cannot start a transaction within a transaction`.
   The doc now states plainly: a migration file is plain SQL, no `BEGIN`/`COMMIT`.
2. **Bare `node` cannot run the scripts.** `node db/migrate.ts` failed on `@/lib/env` and on
   extensionless imports — `node` reads neither `tsconfig` paths nor extensionless specifiers.
   Scripts now run through `tsx`, and there is a rule saying so.
3. **Missing `.env`.** `lib/env.ts` validates `SESSION_SECRET` and throws before touching the
   database, so the failure looks like a DB bug. `db:migrate` now passes
   `--env-file-if-exists=.env`, and `scaffold.sh` writes a dev `.env`.
4. **`node --test tests/unit`** → `ERR_UNSUPPORTED_DIR_IMPORT`. The test script now targets a
   glob: `node --import tsx --test "tests/unit/**/*.test.ts"`.
5. **A dangling import** — `invoice-list.tsx` imported `@/db/queries/invoices` while only
   `users.ts` existed. `invoices.ts` now exists and its table is in the initial migration.

## Not run here, and why

`next build` / `tsc --noEmit` need `next` and `react` installed. The install above was
deliberately limited to `better-sqlite3 zod tsx` to keep the run fast; the DB layer — the part
this document is mostly about — is fully exercised.
