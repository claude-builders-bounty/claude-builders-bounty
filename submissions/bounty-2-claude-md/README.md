# CLAUDE.md Template — Next.js 15 + SQLite SaaS

Production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## Setup (3 steps)

1. Copy `CLAUDE.md` to your project root
2. Adjust stack versions if needed (Node, pnpm, Next.js)
3. Start coding — Claude Code understands your project conventions immediately

## What's Covered

- **Stack**: Next.js 15, TypeScript 5 (strict), SQLite via better-sqlite3, Drizzle ORM, Tailwind CSS 4, Zod, pnpm
- **Database**: Schema conventions, WAL mode, migration rules, connection singleton, pragma settings
- **Components**: Server Components (default), Client Components (leaf-level only), Server Actions, Forms with `useActionState`
- **Naming**: Consistent conventions for files, components, hooks, tables, columns, env vars
- **Anti-patterns**: 15 explicit "don't do this" rules with reasoning and alternatives
- **Testing**: Vitest + Playwright strategy with coverage requirements

## Design Decisions

Every rule has a reason. Key choices:

| Decision | Reasoning |
|----------|-----------|
| SQLite over PostgreSQL | Zero-config, single file, ACID, no server needed, perfect for SaaS MVP |
| Drizzle over Prisma | Lighter, faster cold starts, SQL-like API, better SQLite support |
| UUIDs over auto-increment | Non-predictable, no entity count exposure, easier data migration |
| Server Components default | SSR, direct DB access, no client-side waterfall requests |
| Server Actions over API routes | Type-safe, automatic revalidation, no manual fetch boilerplate |
| pnpm over npm/yarn | Strict dependency resolution, faster, disk-efficient |

## Testing the Template

Tested by creating a greenfield Next.js + SQLite project, pasting the CLAUDE.md, and confirming Claude Code:

- Understood the folder structure without asking
- Used Server Components by default (no `useEffect` for data)
- Applied correct Drizzle schema conventions (UUIDs, timestamps, WAL mode)
- Used Server Actions for mutations (not API routes)
- Applied Tailwind utilities (no CSS modules)
- Validated with Zod at boundaries
- Followed naming conventions consistently

Closes #2
