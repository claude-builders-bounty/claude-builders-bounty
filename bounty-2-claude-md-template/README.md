# Bounty #2: CLAUDE.md for Next.js 15 + SQLite SaaS

Production-ready, opinionated `CLAUDE.md` template for SaaS applications built with Next.js 15 App Router and SQLite.

## Quick Start

```bash
# 1. Create your Next.js project
pnpm create next-app@latest my-saas --typescript --tailwind --eslint

# 2. Drop in the CLAUDE.md
cp CLAUDE.md my-saas/CLAUDE.md

# 3. Start building with Claude Code
cd my-saas && claude
```

No modification needed. Claude Code reads the file and understands the full project context.

## What Makes This Different

This template goes beyond basic project conventions. It covers the full Claude Code feature set:

| Section | What Competitors Cover | What This Template Covers |
|---------|----------------------|--------------------------|
| Stack | Package list | Pinned versions with rationale for each choice |
| Structure | Folder tree | File organization rules, co-location policy, size limits |
| Database | Basic SQL examples | SQLite-specific optimizations (WAL, INTEGER PK, Unix timestamps), Drizzle schema templates, migration iron laws |
| Components | Server vs Client | Full patterns with `useActionState`, Server Actions as primary mutation layer |
| Validation | "Use Zod" | Shared schema pattern between client/server with type inference |
| Auth | "Use NextAuth" | Lucia session-based auth with Argon2id, anti-JWT rationale |
| Anti-patterns | 3-5 items | 13 anti-patterns with specific alternatives and reasoning |
| Hooks | Not covered | PreToolUse (destructive command blocking), PostToolUse (auto-format), Stop (quality gate) |
| MCP Servers | Not covered | Filesystem and SQLite MCP server configuration |
| Permissions | Not covered | Plan mode vs auto-accept with allow/deny lists |
| Memory | Not covered | Session-persistent memory system for decisions and constraints |
| Agents | Not covered | Multi-agent orchestration patterns for complex tasks |
| Testing | "Write tests" | Full TDD workflow, test structure, coverage targets, no-mock DB policy |
| Common Tasks | Not covered | Step-by-step playbooks for adding tables, pages, and actions |

## Testing the Template

To verify Claude Code understands the context without clarifying questions, try these prompts:

```
> "Add a projects table with name and description"
Expected: Creates Drizzle schema, generates migration, adds validators, creates Server Actions, writes tests.

> "What ORM should I use?"
Expected: References Drizzle with specific reasoning (zero runtime, sync API for SQLite).

> "Add a settings page"
Expected: Creates Server Component in (dashboard) group, fetches data directly from DB, extracts forms into Client Components.

> "How should I hash passwords?"
Expected: References Argon2id via @node-rs/argon2, explains why not bcrypt.
```

## File Structure

```
bounty-2-claude-md-template/
├── CLAUDE.md    # The template (drop into any Next.js + SQLite project)
└── README.md    # This file
```

## Acceptance Criteria

- [x] Covers: project structure, naming conventions, DB migration rules
- [x] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated: every rule has a documented reason
- [x] Usable without modification on a greenfield Next.js + SQLite project
- [x] Tested: Claude Code understands context without clarifying questions

## Bonus Coverage (Beyond Requirements)

- [x] Claude Code hooks (PreToolUse, PostToolUse, Stop)
- [x] MCP server configuration (filesystem, SQLite)
- [x] Permission modes (plan mode, auto-accept with scoped allows)
- [x] Memory system for cross-session persistence
- [x] Agent orchestration patterns
- [x] TDD workflow with coverage targets
- [x] Security checklist
- [x] Performance targets
- [x] Common task playbooks
- [x] Git conventions

Closes #2
