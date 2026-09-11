# Next.js 15 + SQLite SaaS — CLAUDE.md template

Opinionated [CLAUDE.md](./CLAUDE.md) for greenfield B2B SaaS projects.

## Install (2 commands)

```bash
mkdir -p your-saas && cd your-saas
npx create-next-app@latest . --ts --tailwind --app --src-dir --eslint
cp /path/to/CLAUDE.md ./CLAUDE.md
```

## Verify Claude Code understands the context

1. Open the new project in Claude Code with this `CLAUDE.md` at the repo root.
2. Ask: *"Add a Drizzle schema for `projects` with workspace scoping. Where do files go and what migration command do I run?"*
3. Expected: references `src/db/schema/`, `drizzle-kit generate/migrate`, server-only db client, snake_case tables — **without** asking where to put database code.

## Sections included

- Stack and versions
- Folder structure
- SQL / migration conventions
- Component patterns
- Dev commands
- What we don't do (with reasons)
