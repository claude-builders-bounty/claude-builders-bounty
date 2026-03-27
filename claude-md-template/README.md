# Next.js 15 + SQLite SaaS — CLAUDE.md Template 📋

An opinionated, production-ready `CLAUDE.md` for Claude Code. Drop it into any greenfield Next.js 15 + SQLite project and Claude will understand the full context without asking clarifying questions.

## What's inside

| Section | What it covers |
|---------|---------------|
| **Stack & Versions** | Pinned versions: Next 15, React 19, Drizzle, better-sqlite3, Tailwind 4, TS 5.7 |
| **Folder Structure** | Route groups, components, db, lib, server actions, validators |
| **SQL Conventions** | UUIDs, timestamps as integers, soft delete, Drizzle schema patterns |
| **Migrations** | `drizzle-kit generate` → `drizzle-kit migrate` — never edit manually |
| **Component Patterns** | Server Components default, `'use client'` only when needed |
| **Server Actions** | Zod validation, structured error returns, `revalidatePath` |
| **Dev Commands** | `dev`, `build`, `db:generate`, `db:migrate`, `db:studio`, `lint`, `typecheck` |
| **Anti-Patterns** | 10 "What we don't do" rules with reasons (no Prisma, no `any`, no CSS files) |
| **Error Handling** | `error.tsx` + `loading.tsx` in every route group |

## Install (1 command)

```bash
cp claude-md-template/CLAUDE.md /path/to/your/project/CLAUDE.md
```

That's it. Claude Code will automatically read it on project open.

## Design Philosophy

Every rule has a reason:

- **Drizzle over Prisma** → No runtime bloat, no cold start penalty, type-safe SQL
- **UUIDs over auto-increment** → Merge-safe, non-guessable, works across DB replicas
- **Soft delete over hard delete** → Audit trail, accidental deletion recovery
- **Named exports over default** → Better IDE refactoring, grep-ability
- **Co-located tests** → Find `UserAvatar.test.tsx` next to `UserAvatar.tsx`
- **No barrel exports** → Avoids circular dependencies and tree-shaking issues

## Tested

Created a fresh Next.js 15 project, added this CLAUDE.md, and confirmed Claude Code:
1. ✅ Understands the stack without asking
2. ✅ Generates components using Server Components by default
3. ✅ Uses Drizzle schema patterns from the template
4. ✅ Follows the folder structure conventions
5. ✅ Applies soft-delete pattern automatically

## License

MIT
