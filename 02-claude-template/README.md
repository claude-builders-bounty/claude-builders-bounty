# Next.js + SQLite CLAUDE.md Template

A production-ready, opinionated `CLAUDE.md` for Next.js 15 App Router + SQLite SaaS projects. Drop it into any greenfield project and Claude Code immediately understands your conventions.

## Quick Start

```bash
# 1. Copy to your project root
cp CLAUDE.md /path/to/your-nextjs-project/CLAUDE.md

# 2. Verify Claude Code picks it up
# Open Claude Code in your project — it should reference rules from CLAUDE.md
# without asking clarifying questions about stack, structure, or conventions.
```

## What's Covered

- **Stack**: Next.js 15 App Router, SQLite (better-sqlite3/Turso), Drizzle ORM, Tailwind v4, TypeScript strict, NextAuth v5
- **Folder structure**: Clear separation of app/, components/ui/, components/features/, db/, lib/, server/actions/
- **SQL conventions**: snake_case, UUID PKs, soft deletes, migration discipline
- **Component patterns**: Server-first, Client leaf nodes, Server Actions for forms
- **Anti-patterns**: 10+ rules covering what NOT to do (no pages/, no any, no raw SQL, no useEffect data fetching)

## Philosophy

Every rule in this CLAUDE.md exists for a reason:
- **No barrel exports from components/** — prevents bundling unused shadcn/ui components
- **UUID primary keys** — avoids sequential ID enumeration attacks
- **Soft deletes** — GDPR compliance and data recovery
- **Server Actions over API routes** — progressive enhancement with zero JS fallback

## Testing the Template

1. Create a new Next.js project: `npx create-next-app@latest test-app`
2. Copy `CLAUDE.md` into the project root
3. Open Claude Code and ask: "What stack and conventions should I follow for forms?"
4. Claude should answer with Server Actions, Zod validation, and the specific patterns from this file — without asking clarifying questions.
