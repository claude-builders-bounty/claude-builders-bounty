# CLAUDE.md 鈥?Next.js 15 + SQLite SaaS Starter

A production-ready `CLAUDE.md` for greenfield Next.js 15 SaaS projects using SQLite (better-sqlite3). Drop it in and Claude Code immediately understands your stack, conventions, and patterns 鈥?no clarifying questions needed.

## Quick Start

```bash
# Copy into your Next.js project root
cp CLAUDE.md /path/to/your-nextjs-project/CLAUDE.md
```

That's it. Claude Code will read it on next invocation.

## What's Covered

- **Stack & versions** 鈥?Next.js 15, better-sqlite3, Drizzle ORM, Lucia Auth, Tailwind CSS v4, shadcn/ui, Zod, Stripe, Resend
- **Project structure** 鈥?App Router conventions with `(marketing)` and `(dashboard)` route groups
- **Naming conventions** 鈥?Files, components, server actions, DB tables, Zod schemas
- **Database conventions** 鈥?Migration workflow, schema rules, soft-delete preference
- **Component patterns** 鈥?Server components by default, client components explicit, server actions for mutations
- **Auth pattern** 鈥?Lucia v3 with Drizzle adapter
- **Anti-patterns** 鈥?What we NEVER do (and why)
- **Dev commands** 鈥?Build, lint, typecheck, db operations, testing
- **Environment variables** 鈥?Required keys with examples

## Design Philosophy

Every rule has a reason. No convention exists "just because."

- **Server component first** 鈫?better performance, less JS shipped
- **Server Actions over API routes** 鈫?zero serialization overhead, types flow
- **Soft-delete over hard-delete** 鈫?users make mistakes, keep the data
- **Zod before DB** 鈫?validate at the boundary, not in the query

## License

MIT
