# Next.js 15 + SQLite CLAUDE.md template

An opinionated, production-ready `CLAUDE.md` for a SaaS project on Next.js 15 (App Router) + SQLite (`better-sqlite3` or Turso).

Submitted for [claude-builders-bounty issue #2](../../issues/2).

## Use it

```bash
# In a fresh Next.js project:
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claudemd/CLAUDE.md > CLAUDE.md
```

Or just **copy [`CLAUDE.md`](CLAUDE.md)** into the root of your project. That's the whole template. No build step.

## What's in it

A real `CLAUDE.md`, not a generic boilerplate. Every rule has a reason. Sections:

1. **Stack** — pinned versions, package manager (pnpm), and the libraries we deliberately do *not* use
2. **Folder structure** — Next 15 App Router with `(marketing)` / `(app)` route groups, `db/` and `server-actions/` siblings, naming conventions
3. **Database conventions** — forward-only migrations, mandatory FKs, INTEGER timestamps, prepared statements, transaction rules
4. **Component patterns** — Server Components by default, Server Actions over API routes, discriminated-union results, no `useEffect` data fetching
5. **Environment variables** — single `lib/env.ts` choke point, Zod-parsed at boot
6. **Dev commands** — `pnpm` script names matching what most repos already have
7. **What we don't do, and why** — the opinionated section. ORMs, JWT sessions, CSS-in-JS, barrel files, silent catches. Each one has the reason.
8. **Workflow conventions** — branches, conventional commits, PR description shape

## Why opinionated, not generic

Generic CLAUDE.md files produce generic Claude output. The point of this file is to *narrow* Claude's choices to the conventions the team has already settled on, so a new feature can be implemented in one shot without "should I use a server action or an API route?" coming up every time.

If a rule in the file does not match the team's actual practice, edit that rule. The file is a living document. The default opinions are calibrated for:

- A small team (1-5 people) shipping a paid SaaS product
- SQLite chosen deliberately for operational simplicity
- App Router (not Pages Router)
- TypeScript strict
- Server-first React

If you are on Pages Router, use `pages/`, or use Postgres + Drizzle, this template is the wrong starting point. Forks welcome.

## How it was tested

Pasted into a freshly generated `pnpm dlx create-next-app@latest` project (App Router, TypeScript, Tailwind, ESLint). Started a Claude Code session in the project root with the prompt:

> Add a `users` table with id, email, hashed_password, created_at, updated_at. Then add a Server Action `signUp(email, password)` that inserts a row. Then add a sign-up form at `/sign-up` that calls the action.

Claude produced the migration with the right column types (INTEGER timestamps, NOT NULL, the boilerplate trigger for `updated_at`), the typed query function in `db/queries/users.ts`, the Server Action returning a `Result<{ id: number }>` discriminated union, the form as a `<form action={signUp}>` Server Component, and zero `useEffect` calls. No clarifying questions asked.

That is the bar: a greenfield Claude Code session reads `CLAUDE.md` and produces code that fits the conventions on the first try.

## License

MIT — same as the parent repo.
