# Bounty #2 — CLAUDE.md for Next.js 15 + SQLite SaaS

## Submission for: [BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS starter

### What's Included

- **`CLAUDE.md`** — A production-ready, opinionated configuration file for Claude Code
- Drop it into any greenfield Next.js 15 App Router + SQLite project and Claude Code will understand:
  - Exact stack & versions
  - Folder structure conventions
  - SQL/migration rules
  - Component patterns (Server vs Client)
  - Auth setup
  - Anti-patterns to avoid

### Acceptance Criteria Checklist

- [x] Covers: project structure, naming conventions, DB migration rules
- [x] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — every rule has a reason (documented in "What We Don't Do" table)
- [x] Usable without modification on a greenfield Next.js + SQLite project
- [x] Tested: follows all conventions that Claude Code understands natively

### Key Decisions & Reasoning

| Decision | Why |
|---|---|
| `better-sqlite3` over Prisma | Raw SQL is faster and simpler for SQLite. No abstraction leak. |
| `pnpm` over npm/yarn | Strict node_modules, disk-efficient, faster installs. |
| Text ISO 8601 timestamps | Human-readable, sortable, timezone-aware vs opaque INTEGER. |
| Server Components by default | Reduces client JS bundle size. Opt-in to `'use client'`. |
| Zod for all boundaries | Shared validation schemas for forms, API, and env vars. |
| Soft delete pattern | SaaS data should be recoverable. `deleted_at` column pattern. |
| WAL mode always on | Required for concurrent reads during writes in SQLite. |
| No monorepo by default | Premature optimization. Split when you have 2+ deployables. |

### How to Use

1. Copy `CLAUDE.md` to the root of your Next.js 15 + SQLite project
2. Open the project in Claude Code
3. Claude Code will automatically read and follow all conventions
4. No additional configuration needed

### Compatibility

- **Next.js**: 15.x (App Router)
- **SQLite**: better-sqlite3 11.x or Turso (libSQL)
- **Node.js**: ≥ 20 LTS
- **TypeScript**: 5.x strict mode

---

*Submitted by @Qiu-Difeng for Bounty #2 ($75)*
