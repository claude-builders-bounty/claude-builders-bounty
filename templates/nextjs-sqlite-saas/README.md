# Next.js 15 + SQLite SaaS Template Blueprint for Claude Code 🚀

An opinionated, production-ready `CLAUDE.md` architecture template designed for rapid SaaS development with Next.js 15 App Router, React 19, SQLite (`better-sqlite3` / Turso libSQL), and Drizzle ORM.

```
                  Next.js 15 App Router Shell
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     React Server Components        Client Boundary Leaf Nodes
     • Direct DB Queries             • Minimal 'use client'
     • Zero Waterfall Latency        • Interactive state only
               │
               ▼
     Server Actions Boundary
     • Zod input validation
     • Discriminated union return
               │
               ▼
     Drizzle ORM + SQLite (WAL Mode)
     • better-sqlite3 (VPS / local) or @libsql/client (Turso)
     • Foreign Keys ON, 5000ms busy timeout
```

---

## 📦 How to Use

Drop `CLAUDE.md` into the root of any new or existing Next.js + SQLite repository:

```bash
curl -sSL https://raw.githubusercontent.com/zarya8096-max/claude-builders-bounty/main/templates/nextjs-sqlite-saas/CLAUDE.md -o CLAUDE.md
```

Claude Code will immediately understand your architecture, directory conventions, and coding rules without asking clarifying questions.

---

## 🛠️ Included Starter Assets

To bootstrap a greenfield SaaS project in under 60 seconds, copy the provided blueprints:
- `package.json.example`: Pinned, mutually compatible Next.js 15, React 19, Drizzle, and TypeScript dependencies.
- `drizzle.config.example.ts`: Pre-configured Drizzle Kit configuration targeting `sqlite.db` and `./db/schema`.

---

## ✨ Key Architectural Invariants

1. **Deterministic SQLite Production Setup:** Enforces WAL journal mode, 5000ms busy timeout, and foreign key integrity.
2. **Modular Architecture:** Clear boundary between Server Components (`app/`), Server Actions (`server/actions/`), and Queries (`server/queries/`).
3. **Strict AI Guardrails:** Eliminates common LLM anti-patterns (no unnecessary `'use client'`, no Prisma engine overhead, no unauthenticated SQL).
