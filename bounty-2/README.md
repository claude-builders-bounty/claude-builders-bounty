# Bounty #2: Opinionated CLAUDE.md for Next.js 15 + SQLite SaaS

## Usage

Drop `CLAUDE.md` into the root of any greenfield Next.js 15 App Router + SQLite project. It serves as a coding constitution for both human developers and AI coding assistants (Claude, Cursor, etc.).

### What's Inside

- **Stack & Versions** — Pin exact versions. No drift.
- **Folder Structure** — App Router route groups, colocated components, pure lib/.
- **SQL & Migrations** — Forward-only numbered migrations, prepared statements, no ORM.
- **Component Patterns** — Server Components by default, `'use client'` only when necessary.
- **Server Actions** — Zod validation, revalidation, colocated with routes.
- **Dev Commands** — Turbopack, separate migrate script, pre-commit checks.
- **Naming** — kebab-case files, PascalCase components, snake_case SQL columns.
- **Anti-patterns** — 10 things we don't do and the hard-won reasons why.

### Quick Start

1. Copy `CLAUDE.md` to your project root
2. Set up `package.json` scripts as documented
3. Create `db/` folder structure with `client.ts` and `migrations/`
4. Start coding — the file is your constitution

### Philosophy

Every rule has a reason. Not "because best practice" — because something broke, something was slow, or something was unmaintainable. This isn't a generic style guide. It's a battle-tested set of decisions for a specific stack.
