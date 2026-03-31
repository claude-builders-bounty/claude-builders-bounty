# CLAUDE.md for Next.js + SQLite SaaS

> Opinionated, production-ready CLAUDE.md for Next.js 15 App Router + better-sqlite3 projects.

## Quick Start

```bash
# 1. Copy CLAUDE.md to your project root
# 2. Ask Claude Code to read it
# 3. Start building
```

## What's Inside

- **Stack**: Next.js 15 + better-sqlite3 + Tailwind + TypeScript
- **No ORM**: Hand-written SQL for full control
- **Opinionated**: Every rule has a reason
- **Production-ready**: Based on real project experience

## Key Principles

1. **Database**: Use `better-sqlite3` with WAL mode
2. **No ORM**: Write SQL directly
3. **Server First**: Use Server Components when possible
4. **Simple**: Prefer duplication over wrong abstraction

## File Structure

```
app/           # Next.js App Router
lib/db.ts      # Database connection
lib/schema.sql # Database schema
components/    # React components
```

## Usage

1. Copy `CLAUDE.md` to your project
2. Claude Code will understand your conventions
3. No clarifying questions needed

## Tested

✅ Created new project, pasted CLAUDE.md, Claude understood context immediately.

## License

MIT
