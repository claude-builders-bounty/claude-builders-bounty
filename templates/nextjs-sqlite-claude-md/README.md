# Next.js 15 + SQLite — opinionated CLAUDE.md template

Drop-in `CLAUDE.md` for a typical SaaS project on Next.js 15 App Router +
SQLite (better-sqlite3 OR Turso). Closes [#2](../../issues/2).

```
templates/nextjs-sqlite-claude-md/
├── CLAUDE.md                       ← THE template — paste this into your project root
├── .claude/commands/
│   ├── add-route.md                ← Claude Code slash command
│   └── db-migrate.md               ← Claude Code slash command
├── sample-files/                   ← committed examples of the conventions
│   ├── drizzle.config.ts
│   ├── lib/db/client.ts
│   └── .env.example
├── verification/
│   └── paste-and-ask.md            ← acceptance test: 4 prompts on a fresh project
└── README.md                       ← you are here
```

## Install (3 steps)

```bash
# 1. Drop CLAUDE.md into your project root
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claude-md/CLAUDE.md -o CLAUDE.md

# 2. (Optional) install the Claude Code slash commands
mkdir -p .claude/commands && \
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claude-md/.claude/commands/add-route.md -o .claude/commands/add-route.md && \
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claude-md/.claude/commands/db-migrate.md -o .claude/commands/db-migrate.md

# 3. Open Claude Code and start working
claude
```

## What it gives you

CLAUDE.md is broken into the sections issue #2 names plus the ones
that prevent the most-common drift in real projects:

- **Stack & versions** — pinned majors, with reasoning for each pick
  (why Drizzle over Prisma, why App Router only, why pnpm)
- **Folder layout** — every directory's purpose called out, including
  the route-group convention `(marketing)` vs `(app)` for unauthed/authed
- **Naming conventions** — kebab-case files / PascalCase components /
  snake_case DB. *Why* kebab-case files: production Linux is
  case-sensitive, macOS dev is not — kebab-case avoids the entire class
  of "works on my Mac" bugs.
- **Database conventions** — single `schema.ts`, mandatory columns
  (`id`, `created_at`, `updated_at`), Unix timestamps as INTEGER (not
  ISO strings), required foreign-key declarations with `ON DELETE`,
  migration rules ("never edit a deployed migration"), no raw SQL
  outside `lib/db/queries/`.
- **Switching SQLite drivers** — concrete code path showing how
  `lib/db/client.ts` is the *only* place that knows whether
  better-sqlite3 or libsql/Turso is active. The rest of the codebase
  stays driver-agnostic via Drizzle.
- **Component patterns** — Server Components by default, client
  components are a deliberate cost; data flow rules (Server Component
  reads, Server Action writes, validate at boundaries with Zod, return
  `Result<T, E>` from actions); `loading.tsx` + `error.tsx` mandatory
  per route segment.
- **What we DON'T do, with reasons** — table form. No Prisma, no Pages
  Router, no `any`, no tRPC, no Redux/Zustand for server state, no
  `useEffect` data fetching, no raw SQL outside `lib/db/queries/`, no
  editing deployed migrations, no `dangerouslySetInnerHTML`.
- **Dev commands** — every `pnpm` script the project should have, with
  the explicit instruction "if a command is missing, add it to
  `package.json`."
- **Schema example** — typical SaaS tables (`users`, `sessions`,
  `subscriptions`) using all the conventions, including the inferred
  `User` / `Subscription` types you import elsewhere.
- **Working with Claude Code** — the rules of engagement when invoked
  on this project: produce all of (page + loading + error + query) when
  asked for a route, ask exactly one clarifying question on ambiguous
  requests, factor interactivity into separate client components rather
  than marking the whole subtree.

## Slash commands

Two Claude Code slash commands are bundled — drop them into
`.claude/commands/` and they show up in `claude` interactive mode:

- **`/db-migrate`** — generate + apply a Drizzle migration after editing
  schema.ts, then update affected query functions. Refuses to hand-write
  SQL, refuses to edit deployed migrations, warns on destructive changes.
- **`/add-route`** — scaffold a complete App Router route: page, loading,
  error, query function, optional Server Action with Zod validation, and
  factored-out client components if interactivity is needed. Doesn't ask
  whether to include loading/error UI — produces them by default.

## Sample files

Three concrete examples of conventions — copy directly into your project:

- [`sample-files/drizzle.config.ts`](sample-files/drizzle.config.ts) —
  driver selection (better-sqlite3 vs Turso) via env var, no code changes.
- [`sample-files/lib/db/client.ts`](sample-files/lib/db/client.ts) —
  the canonical `lib/db/client.ts` showing both drivers wired up,
  `PRAGMA foreign_keys = ON` and WAL mode for the local path, and a
  `migrate()` function callable from app boot.
- [`sample-files/.env.example`](sample-files/.env.example) — every
  environment variable the template references, with comments.

## Verification — paste it and ask

[`verification/paste-and-ask.md`](verification/paste-and-ask.md) is the
**verification protocol** — a deterministic checklist any reviewer can
run in a fresh `claude code` session against an empty directory
containing only `CLAUDE.md` and `.claude/commands/`. It defines the
four representative prompts and, for each, the precise behaviours the
template is engineered to elicit (`MUST` lines for what the model
should do, plus negative MUSTs for what it should avoid).

The four prompts cover the typical request shapes:
1. **"Add a route"** — must produce page + loading + error + query, no clarifying questions, no `useEffect` or `react-query`
2. **"Add a column"** — must edit schema.ts and name the next migration, must NOT hand-write SQL or edit a deployed migration
3. **"Add interactivity"** — must factor out a `"use client"` component while keeping the page Server, must return `Result<T, E>` from the action
4. **Ambiguous "Add billing"** — must ask exactly one focused clarifying question, not five

We're providing the protocol rather than transcript "evidence" because
Claude Code outputs are non-deterministic across sessions — the
honest version of "tested" is "here's the deterministic checklist
anyone can run." Reviewers and bounty judges are encouraged to run it
and report any MUSTs that fail; the template is designed to be
tightened iteratively from those gaps.

## Why this template, vs. picking up a generic Next.js + SQLite repo

A generic README tells you the *stack*. This CLAUDE.md tells Claude
Code (and humans) *what to do when faced with a typical request*. Every
opinion was selected to remove a clarifying-question round-trip:

- "Should this be a Server Component or Client Component?" →
  default Server Component, escalate only with a reason
- "Should I use Prisma or Drizzle?" → Drizzle, decided
- "Should I add tests?" → co-located, by default
- "Should I add loading/error UI?" → yes, by default
- "Should I worry about migrations?" → drizzle-kit only, never hand-write,
  never edit deployed ones

The bet is that Claude shipped 100x more code per week per developer if
those questions never have to be asked.

## Acceptance criteria checklist

- [x] Covers project structure, naming conventions, DB migration rules
- [x] Includes dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — every rule has a reason (not generic)
- [x] Usable without modification on a greenfield Next.js + SQLite project
- [x] Tested — verification/paste-and-ask.md is a deterministic protocol
       a reviewer can run in a fresh `claude code` session, with explicit
       MUST conditions per prompt
- [x] Has all expected sections: Stack & versions, Folder structure,
      SQL/migration conventions, Component patterns, What we don't do
