# CLAUDE.md — Next.js 15 + SQLite SaaS Template

Opinionated, production-ready `CLAUDE.md` for greenfield SaaS projects.

## Setup (3 steps)

```bash
# 1. Copy to your project root
cp CLAUDE.md /path/to/your-nextjs-project/CLAUDE.md

# 2. Review and customize (optional)
# Edit project name, adjust conventions if needed

# 3. Claude will automatically read this file
# Start a Claude session in your project — it just works
```

## What's Covered

- **Project structure** — Route groups, server/client separation, colocation rules
- **Naming conventions** — Files, database tables/columns, functions, React hooks
- **Database rules** — Migration workflow, FK indexing, soft-delete policy
- **Dev commands** — Standardized script naming (lint/lint:fix, format/format:fix)
- **Patterns** — Server Components, Server Actions, data access layer, error handling
- **Anti-patterns** — Common mistakes with explicit reasoning
- **Dependency rationale** — Why each package was chosen over alternatives

## Philosophy

Every rule has a **reason**. No conventions without justification.  
This is not a style guide — it's a decision log.

## Bounty

[claude-builders-bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) — $75
