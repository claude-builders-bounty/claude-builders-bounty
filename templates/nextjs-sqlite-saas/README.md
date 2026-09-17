# Next.js 15 + SQLite SaaS Template (`CLAUDE.md`)

This template provides an opinionated, production-ready `CLAUDE.md` configuration specifically designed for greenfield SaaS projects leveraging Next.js 15 App Router and SQLite / LibSQL / Drizzle ORM.

---

## 🎯 What is this?

When initializing a new AI-assisted project with Claude Code, dropping this `CLAUDE.md` into your root workspace gives Claude immediate, deterministic understanding of:
- The exact project structure, routing conventions, and naming standards.
- Safe SQLite migration workflows via Drizzle Kit.
- Best practices for React Server Components (RSC) and type-safe Server Actions with Zod.
- Architectural boundaries and explicit anti-patterns.

---

## 🚀 How to Use

1. Copy `CLAUDE.md` to the root of your Next.js SaaS repository:
   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/my-saas-project/CLAUDE.md
   ```
2. Launch Claude Code:
   ```bash
   claude
   ```
3. Claude Code will automatically ingest the guidelines and build features complying with your architectural rules without requiring back-and-forth prompt clarifications.
