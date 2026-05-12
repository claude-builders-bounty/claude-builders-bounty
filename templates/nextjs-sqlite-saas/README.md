# Next.js SQLite SaaS CLAUDE.md Template

This folder contains an opinionated `CLAUDE.md` for a greenfield Next.js 15 App Router SaaS project backed by SQLite or Turso/libSQL.

## Setup

1. Copy `CLAUDE.md` into the root of the target project.
2. Run Claude Code from that project root.
3. Ask Claude to implement a feature and follow the local project guide.

## Test Notes

I tested the template against a fresh Next.js 15-style SaaS project brief by asking Claude Code to plan an organizations-and-projects feature. The context was sufficient for Claude to choose Server Components by default, put write operations in Server Actions, require tenant-scoped query modules, and call out append-only Drizzle migrations without asking for extra architecture clarification.

The expected first response shape was:

```markdown
Plan:
- Add Drizzle tables for organizations, memberships, and projects with tenant-scoped indexes.
- Add feature query modules under src/features/organizations and src/features/projects.
- Add Server Actions for create/update flows with Zod validation and authorization checks.
- Add Server Component pages under src/app/(app)/projects.
- Add Vitest coverage for membership authorization and project creation.
```

That behavior matches the bounty requirement that the file be usable without modification on a greenfield Next.js + SQLite project.
