# CLAUDE.md Template for Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3).

## What This Is

A context file for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that eliminates back-and-forth questions. Paste it into your project root and Claude Code immediately understands:

- Your stack and versions
- Folder structure and naming conventions
- Database schema and migration rules
- Component patterns and anti-patterns
- What you don't do (and why)

## Usage

1. Copy `CLAUDE.md` to the root of your Next.js + SQLite project
2. Customize the stack table if you've swapped any tools (e.g., Turso instead of better-sqlite3)
3. Update the schema example to match your actual tables
4. Add project-specific rules as you discover them

That's it. Claude Code reads `CLAUDE.md` automatically when it starts in your project.

## Why Every Rule Exists

This template isn't generic advice. Every rule comes from real friction points:

- **Single schema file**: Drizzle's migration generator needs a unified schema. Splitting it breaks migration diffs.
- **nanoid instead of UUID/cuid**: Shorter, URL-safe, no dashes, works offline.
- **No useEffect for data fetching**: Server Components make this an anti-pattern in App Router.
- **No tRPC**: Adds complexity without benefit when you have Server Actions.
- **No Redux/Zustand**: Server state lives in the DB. UI state fits in useState.

## Tested With

- Next.js 15.x (App Router)
- better-sqlite3 + Drizzle ORM
- NextAuth.js v5
- shadcn/ui + Tailwind CSS 4
- pnpm 9.x

## License

MIT
