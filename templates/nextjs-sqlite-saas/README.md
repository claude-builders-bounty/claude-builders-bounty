# Next.js 15 + SQLite SaaS — CLAUDE.md template

An opinionated operating manual for a greenfield Next.js 15 App Router + SQLite SaaS project.
Drop `CLAUDE.md` at the repository root and Claude Code stops asking what the conventions are.

**Stack:** Next.js 15 (App Router), React 19 Server Components, TypeScript strict, Tailwind v4,
`better-sqlite3` with hand-written numbered SQL migrations, Zod, `node --test` + Playwright.
No ORM.

## Use it

```bash
cp CLAUDE.md /path/to/your/repo/CLAUDE.md
```

That is the whole install. There is no placeholder to fill in.

## Check it (2 commands)

```bash
node verify.mjs                       # 53 checks: sections, reasons, paths, scripts
bash scaffold.sh /tmp/check && cd /tmp/check && npm i better-sqlite3 zod tsx && npm run db:migrate
```

`verify.mjs` scaffolds the exact tree the document describes and asserts the doc matches reality —
every documented path exists, every documented `npm run` is a real script, the migration runner is
the one in the doc, and no rule is missing its reason.

## What it covers

- **Stack & versions** — pinned, and why each choice is the right one here
- **Folder structure** — concrete paths, route groups for the auth boundary
- **Naming conventions** — files, components, tables, columns, route params
- **Database rules** — the full migration contract, one prepared-statement pattern, pragmas
- **Component patterns** — server-first, where mutations live, how auth is enforced
- **What we don't do, and why** — 16 anti-patterns, each with its consequence
- **Definition of done** — the exact commands that gate a change

Every rule carries a `because`. A rule without a reason is a rule Claude will drop the moment it
becomes inconvenient.

## Why this beats a generic CLAUDE.md

- **It is decisive.** "Use an ORM or not?" is answered. So is `SELECT *`, and `useEffect` fetching.
- **It encodes two real failure modes** found by actually running the scaffold: nested migration
  transactions, and bare `node` not resolving `tsconfig` paths. See `VERIFIED.md`.
- **It is testable**, which is rare for a prose artifact — `verify.mjs` fails if the doc and the
  scaffold drift apart.
