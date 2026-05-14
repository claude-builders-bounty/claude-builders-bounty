# CLAUDE.md — Next.js 15 + SQLite SaaS Template

An opinionated, production-ready `CLAUDE.md` for a Next.js 15 App Router + SQLite (better-sqlite3/Turso) SaaS project.

## What's Included

- 📁 **Folder structure** — domain-separated, testable, scalable
- 📝 **Naming conventions** — kebab-case files, PascalCase components, snake_case DB columns
- 🗄️ **SQL / migration rules** — Drizzle ORM best practices for SQLite
- 🧩 **Component patterns** — Server Components by default, minimal client JS
- 🔐 **Auth pattern** — NextAuth.js v5, session in layout, not per-page
- 🚫 **Anti-patterns** — 7 things we don't do (and why)
- ✅ **Testing strategy** — Vitest + Playwright, no React Testing Library

## Usage

1. Create your Next.js 15 project
2. Copy `CLAUDE.md` to the project root
3. Claude Code will automatically read it for context

## Requirements

Requires Claude Code (reads `CLAUDE.md` from project root on startup).

## Design Principles

- **Every rule has a reason** — no cargo-cult conventions
- **Zero-config starts** — works on a greenfield project without modification
- **Opinionated but documented** — you can change anything, but know what you're trading off
