# CLAUDE.md Template for Next.js 15 + SQLite SaaS

This submission provides an opinionated, production-ready `CLAUDE.md` template
for a greenfield SaaS project using Next.js 15 App Router and SQLite.

## Use in 3 steps

1. Copy the template into the target project root:
   ```bash
   cp CLAUDE-nextjs15-sqlite.md /path/to/project/CLAUDE.md
   ```
2. Adjust only concrete project names or commands if the project differs from the
   default `pnpm` + Drizzle setup.
3. Start Claude Code in the project root and ask it to inspect `CLAUDE.md` before
   editing.

## What the template covers

- Stack and versions
- Folder structure
- Naming conventions
- Server/client boundaries
- SQLite and Drizzle migration rules
- Query/service patterns
- Validation and error handling
- Auth, permissions, and tenancy
- Component patterns
- Dev commands
- Patterns to follow
- Anti-patterns to avoid
- PR checklist
- First-response behavior for Claude Code

## Test notes

I checked the template against the bounty acceptance criteria and a simulated
greenfield project layout. The file gives Claude Code enough context to proceed
without asking broad architecture questions because it specifies the stack,
folders, migration policy, mutation flow, auth boundaries, validation rules,
commands, and anti-patterns.
