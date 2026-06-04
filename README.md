// markdown
# CLAUDE.md — Next.js 15 + SQLite SaaS Template
 
An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.
 
## Setup
 
**1.** Create a new Next.js project:
 
```bash
pnpm create next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
2. Install dependencies:
// bash
cd my-saas
pnpm add better-sqlite3 drizzle-orm lucia
pnpm add -D drizzle-kit @types/better-sqlite3
3. Copy  CLAUDE.md  to your project root:
// bash
cp ../CLAUDE.md ./CLAUDE.md
That's it — Claude Code will now understand your project conventions without asking clarifying questions.
What's Covered
┌─────────────────────────────┬──────────────────────────────────────────────────┐
│ Section                     │ What it includes                                 │
├─────────────────────────────┼──────────────────────────────────────────────────┤
│ Stack & Versions            │ Exact package versions, runtime, package manager │
│ Folder Structure            │ Feature-grouped App Router layout                │
│ SQL / Migration Conventions │ Schema rules, migration workflow, query patterns │
│ Component Patterns          │ Server-first, client boundaries, data fetching   │
│ What We Don't Do            │ Anti-patterns with reasoning                     │
│ Dev Commands                │ pnpm scripts for dev, build, test, db            │
│ Commit Conventions          │ Conventional commits format                      │
│ Testing Philosophy          │ Unit vs integration vs e2e strategy              │
└─────────────────────────────┴──────────────────────────────────────────────────┘

Why This CLAUDE.md?
- Opinionated — every rule has a why, not just a what
- Zero-config — drop it in a greenfield project and Claude Code works immediately
- Production-ready — conventions used in real SaaS deployments
