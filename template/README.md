# CLAUDE.md for Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for Next.js 15 App Router projects with SQLite.

## What's Included

- Stack & version requirements
- Folder structure conventions
- Database rules (raw SQL, sequential migrations)
- Component patterns (Server Components by default)
- API route conventions
- Development commands
- Anti-patterns to avoid
- Design decisions with rationale

## Usage

```bash
# Create a new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --app --eslint
cd my-saas

# Copy CLAUDE.md to project root
cp CLAUDE.md my-saas/

# Start Claude Code — it will understand the context
claude
```

## Why This Works

Claude Code reads `CLAUDE.md` at the start of every session. This file establishes:
- Exact tech stack (no ambiguity)
- Folder layout (Claude creates files in the right place)
- Coding patterns (consistent output)
- Anti-patterns (avoids common mistakes)

Tested: Create a project, paste this CLAUDE.md, ask Claude to build a feature. It should produce code that follows all conventions without asking clarifying questions.
