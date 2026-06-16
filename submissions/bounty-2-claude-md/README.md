# Next.js 15 + SQLite SaaS CLAUDE.md — Bounty #2

Production-ready `CLAUDE.md` for greenfield SaaS projects.

## Usage

Copy to your project root:

```bash
cp CLAUDE.md /path/to/your-saas/CLAUDE.md
```

Open the project in Claude Code — it should understand stack, folder layout, migration rules, and anti-patterns without follow-up questions.

## Sections included

- Stack & versions (with rationale)
- Folder structure
- Naming conventions
- SQL / migration conventions
- Component & data-fetching patterns
- Dev commands
- Auth & multi-tenancy rules
- Explicit anti-patterns table
- PR checklist for Claude to enforce

## Validation

Tested against a blank Next.js 15 App Router project: Claude correctly proposes Drizzle migrations, Server Actions, and `workspace_id` scoping when asked to "add workspace creation".