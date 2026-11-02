# Next.js 15 + SQLite SaaS Template for Claude Code

A battle-tested, opinionated `CLAUDE.md` rulebook designed specifically for SaaS applications built with **Next.js 15 (App Router, Server Actions)**, **React 19**, **SQLite (`better-sqlite3` or Turso)**, **Drizzle ORM**, and **Tailwind CSS v4**.

---

## Quickstart

### 1. Copy `CLAUDE.md` to your Project Root
Copy [`CLAUDE.md`](./CLAUDE.md) directly into the root directory of your Next.js SaaS project:

```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-project/CLAUDE.md
```

### 2. Run Claude Code
Launch Claude Code in your project directory:

```bash
claude
```

Claude will automatically ingest `CLAUDE.md` at initialization, aligning all code generation, component design, schema migrations, and commands with this standard.

---

## What Makes This Template Different?

1. **Concrete SQLite Production Configuration**:
   - Explicitly configures Write-Ahead Logging (`WAL` mode), `foreign_keys = ON`, `busy_timeout = 5000`, and `synchronous = NORMAL` in `better-sqlite3`.
   - Prevents the classic `"database is locked"` write-contention bug under concurrent local requests.
2. **Strict Server vs. Client Boundary Rules**:
   - Server Components by default; `"use client"` pushed only to leaf-level interactive nodes.
   - Enforces Zod schema validation on every Next.js 15 Server Action.
3. **Financial Safety Built-in**:
   - Zero floating-point decimals for billing/pricing. All currency stored as integer cents.
4. **Anti-Patterns with Explicit "Why" Explanations**:
   - Guides the AI agent away from common traps (e.g., `useEffect` waterfalls, direct database imports into client bundles, and un-migrated schema mutations).
