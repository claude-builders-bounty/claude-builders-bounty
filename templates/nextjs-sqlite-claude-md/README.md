# CLAUDE.md template — Next.js 15 + SQLite SaaS

An opinionated `CLAUDE.md` for a greenfield Next.js 15 (App Router) + SQLite
(better-sqlite3) SaaS project, **plus the project it describes and a validator that
keeps the two in sync**.

Most CLAUDE.md templates are prose. This one ships with:

| Piece | Why it exists |
| --- | --- |
| `CLAUDE.md` | The working agreement: stack, structure, DB rules, patterns, conventions, anti-patterns — every rule with its reason |
| `fixture/` | A real, minimal project that follows every rule, so "usable without modification" is demonstrable rather than claimed |
| `check.mjs` | Fails when the document drifts from the project (a documented `npm run` script or file path that does not exist) |
| `test/run-tests.sh` | Proves `check.mjs` both passes on the real document and catches drift |
| `TEST-LOG.md` | Output of every documented command, executed against the fixture |

## Setup (3 steps)

1. Create the project and copy the agreement to its root:

   ```bash
   npx create-next-app@latest my-saas --typescript --app --no-tailwind && cd my-saas && cp /path/to/CLAUDE.md .
   ```

2. Adopt the conventions the document assumes — the ones a fresh `create-next-app` does
   not give you (copy them from `fixture/`):

   ```bash
   mkdir -p lib/queries lib/validation db/migrations scripts tests
   cp /path/to/fixture/lib/db.ts lib/ && cp /path/to/fixture/scripts/*.mjs scripts/ && cp /path/to/fixture/db/migrations/*.sql db/migrations/
   ```

3. Start Claude Code in the project. It reads `CLAUDE.md` on the first prompt, so it
   already knows the folder layout, the migration rules and what not to do — no
   clarifying questions about where things belong.

## What the document covers

- **Stack and versions**, with the reason each piece is pinned (and why there is no ORM).
- **Folder structure** where every path has one job: routes in `app/`, SQL in
  `lib/queries/`, schemas in `lib/validation/`, migrations in `db/migrations/`.
- **Dev commands** — the exact scripts, plus the rule that `npm run check` gates done.
- **SQL and migration conventions**: append-only migrations, explicit column lists,
  bound parameters, epoch-millisecond timestamps, WAL and foreign keys on.
- **Component patterns**: Server Components by default, database access only on the
  server, server actions parsed with zod.
- **Naming conventions** table, **What we don't do (and why)**, and a definition of done.

## Verification

```bash
node check.mjs              # document vs fixture: 23 checks
bash test/run-tests.sh      # the validator itself, including drift detection
```

`TEST-LOG.md` is the real output of `npm install`, `db:migrate`, `db:seed`, `db:reset`,
`test`, `typecheck`, `lint`, `check`, `build` and `check.mjs` inside the fixture
(Node 24.19): **4/4 tests pass, lint clean, production build OK**, and the route table
shows `/` and `/api/items` as dynamic (ƒ) because they read the database — the intended
consequence of the "pages that read the DB are dynamic" rule.

### Bugs the fixture's tests caught while writing this

These are why the fixture exists rather than a promise:

1. `better-sqlite3` **aborts the process during teardown** if a `Database` handle is still
   open (`Assertion failed: (env) != nullptr` in `Database::~Database`). It made the suite
   flaky in a way that looked random. Fix: the test process never loads the native module;
   it asks `scripts/inspect.mjs` for a JSON snapshot, and that helper always closes.
2. **`node --test tests/` fails on Node 24** (`Cannot find module '/work/tests'`); the
   runner needs auto-discovery (`node --test`) or a glob. Documented in the command table.
3. **`next lint` is deprecated** and prints a warning that will become an error in Next 16;
   the template uses the ESLint CLI (`eslint .`) with a flat config instead.

## Customising

Change these first, they are the opinionated forks in the road: the ORM decision (the
document forbids one), the timestamp representation (`INTEGER` epoch ms), and the
migration policy (append-only, never edited). Everything else is safe to trim.

## License

MIT, like the rest of this repository.
