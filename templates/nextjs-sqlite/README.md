# Next.js 15 + SQLite SaaS CLAUDE.md Template

A production-ready, highly opinionated `CLAUDE.md` configuration designed for greenfield SaaS applications built with **Next.js 15 (App Router)** and **SQLite (better-sqlite3 / Turso / Drizzle ORM)**.

---

## 🚀 Quick Usage

To equip Claude Code with complete context on a new or existing Next.js + SQLite project:

```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-project/CLAUDE.md
```

Claude Code will immediately adopt:
1. Strict server-first architecture rules (React Server Components + Server Actions).
2. Production SQLite pragmas (`WAL` mode, `busy_timeout = 5000`, `foreign_keys = ON`).
3. Drizzle ORM schema patterns and migration workflows.
4. Hard anti-patterns to avoid (no `any`, no unindexed foreign keys, no client-side DB access).

---

## 📋 Acceptance Criteria Checklist

- [x] **Covers project structure & conventions**: Explicit directory tree and naming rules.
- [x] **Database migration rules**: Drizzle Kit generate, push, and migrate workflows.
- [x] **Includes dev commands**: Complete set for Next.js, Drizzle, and testing.
- [x] **Patterns to follow & Anti-patterns**: Concrete rationale behind every single rule.
- [x] **Opinionated**: Every architectural decision has a clear "why".
- [x] **Usable without modification**: Drop into root as `CLAUDE.md`.

---

## 💳 Bounty Claim Reference
- **Issue**: [#2 - [BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)
- **Claimant**: `lam534410-hub`
- **Payout Details**:
  - PayPal: `lamvukyo3001@gmail.com`
  - EVM: `0x24A2151Ec787a2C5c81412A888c3a9d9eEc3beEA`
