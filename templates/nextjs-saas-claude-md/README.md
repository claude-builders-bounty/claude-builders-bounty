# Next.js 15 + SQLite SaaS Template

Production-ready CLAUDE.md template for Claude Code on Next.js 15 App Router + SQLite projects.

## Installation

```bash
# Copy to your Next.js project root
cp CLAUDE.md /path/to/your/project/
```

That's it! Claude Code will now understand your entire stack.

## What's Included

### Stack & Versions
- Next.js 15.x (App Router)
- Node.js 20.x LTS
- SQLite 3.45+ with better-sqlite3
- NextAuth.js 5.x
- Tailwind CSS 4.x
- React Hook Form + Zod

### Opinionated Patterns
- Folder structure for SaaS
- SQL/migration conventions
- Component patterns (Server vs Client)
- Query patterns with transactions
- Validation schemas shared client/server

### Anti-Patterns Avoided
- No Prisma (async overhead)
- No `useEffect` fetching
- No datetime columns
- No global state management

## Testing

Tested on greenfield Next.js 15 + SQLite projects. Claude Code understands the full context without asking clarifying questions.

## Quick Start

1. Create Next.js 15 project
2. Add better-sqlite3 dependency
3. Copy this CLAUDE.md to project root
4. Start building - Claude knows your patterns

## Requirements

- Next.js 15 App Router
- better-sqlite3 or Turso
- Tailwind CSS
- Zod for validation

## License

MIT